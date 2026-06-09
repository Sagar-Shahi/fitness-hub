"""HTTP views for the Fitness Hub chatbot.

Provides a full-page chat (`/chatbot/`), a JSON API endpoint
(`/chatbot/api/`), and a user-context endpoint (`/chatbot/context/`)
that the floating widget can call on load to show a personalized
welcome line.
"""

import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import ChatSession, ChatMessage
from . import coach_context, personality, responder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(request) -> ChatSession:
    """Return the user's current chat session, creating it if needed."""
    user = request.user if request.user.is_authenticated else None
    if user is not None:
        session, _ = ChatSession.objects.get_or_create(user=user)
        return session

    if not request.session.session_key:
        request.session.save()
    key = request.session.session_key
    session, _ = ChatSession.objects.get_or_create(session_key=key, user=None)
    return session


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@require_GET
def chat_page(request):
    """Render the full chat page."""
    session = _get_or_create_session(request)
    recent = list(
        session.messages.order_by('created_at')[:200]
    )
    ctx = coach_context.build_user_context(request.user)
    ctx = coach_context.hydrate_goal_label(ctx)
    greeting = coach_context.greeting_for_context(ctx)
    return render(request, 'chatbot/chat.html', {
        'session': session,
        'recent': recent,
        'coach_context': ctx,
        'greeting': greeting,
    })


@csrf_exempt
@require_POST
def chat_api(request):
    """Accept JSON `{message: "..."}` and return JSON `{reply, intent, refused, reason, suggestions}`."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest('invalid json')

    text = (payload.get('message') or '').strip()
    session = _get_or_create_session(request)

    if text:
        ChatMessage.objects.create(session=session, role='user', content=text)

    result = responder.respond(text, user=request.user)

    ChatMessage.objects.create(
        session=session,
        role='bot',
        content=result['reply'],
        intent=result['intent'],
    )

    suggestions = _suggestions_for(result['intent'], text)

    return JsonResponse({
        'reply': result['reply'],
        'intent': result['intent'],
        'refused': result['refused'],
        'reason': result['reason'],
        'suggestions': suggestions,
    })


@require_GET
def context(request):
    """Return the user's bot context as JSON. Used by the widget to show a
    personalized greeting before the user sends anything."""
    ctx = coach_context.build_user_context(request.user)
    ctx = coach_context.hydrate_goal_label(ctx)
    return JsonResponse({
        'is_authenticated': bool(request.user.is_authenticated),
        'name': ctx.get('name', ''),
        'goal': ctx.get('goal'),
        'goal_label': ctx.get('goal_label'),
        'streak_days': ctx.get('streak_days', 0),
        'days_since_last': ctx.get('days_since_last'),
        'total_completions': ctx.get('total_completions', 0),
        'total_minutes': ctx.get('total_minutes', 0),
        'is_new': ctx.get('is_new', True),
        'has_active_goal': ctx.get('has_active_goal', False),
        'greeting': coach_context.greeting_for_context(ctx),
    })


# ---------------------------------------------------------------------------
# Quick-reply suggestions
# ---------------------------------------------------------------------------

def _suggestions_for(intent_name: str, user_message: str = '') -> list:
    """Return 3 quick-reply chip strings for a given intent or emotion."""
    msg_l = user_message.lower()
    # If user wants to talk / vent
    if any(kw in msg_l for kw in ('just need to talk', 'need someone to talk', 'can we talk', 'talk to me')):
        return [
            'Tell me about your day',
            'What exercises help with stress?',
            'How do I track my mood?',
        ]
    # If user is emotional, show supportive suggestions
    emotion = personality.detect_emotion(user_message)
    if emotion in ('sad', 'frustrated', 'anxious', 'hurt'):
        return [
            'What exercises help with stress?',
            'Just need to talk',
            'Show me a quick workout',
        ]

    table = {
        'greeting': [
            'Motivate me',
            'What should I do next?',
            'How do I use the app?',
        ],
        'who_are_you': [
            'Motivate me',
            'What should I do next?',
            'Show me chest exercises',
        ],
        'motivation': [
            'Show me chest exercises',
            'Beginner workouts',
            'What should I do next?',
        ],
        'next_step': [
            'Motivate me',
            'Beginner exercises',
            'How do I log a workout?',
        ],
        'where_am_i': [
            'How do I log a workout?',
            'How do I change my goal?',
            'How do I change my password?',
        ],
        'exercise_recommend': [
            'Show me chest exercises',
            'Beginner exercises',
            'Exercises for weight loss',
        ],
        'exercise_info': [
            'Show me beginner exercises',
            'How do I do a push-up?',
            'Common mistakes on squats',
        ],
        'nutrition': [
            'How much protein do I need?',
            'What should I eat before a workout?',
            'What is creatine?',
        ],
        'goal_advice': [
            'How do I change my goal?',
            'Exercises for muscle gain',
            'Exercises for weight loss',
        ],
        'recovery': [
            'Best warm-up routine',
            'How many rest days?',
            'How much sleep do I need?',
        ],
        'app_help': [
            'Where is the Workout Library?',
            'How do I track progress?',
            'How do I change my password?',
        ],
        'deep_app_help': [
            'Where is the Workout Library?',
            'How do I track progress?',
            'How do I change my goal?',
        ],
        'progress_help': [
            'Where is the Records page?',
            'What does the Progress page show?',
            'How do streaks work?',
        ],
        'default': [
            'Motivate me',
            'How do I use the app?',
            'How much protein do I need?',
        ],
    }
    return table.get(intent_name, table['default'])
