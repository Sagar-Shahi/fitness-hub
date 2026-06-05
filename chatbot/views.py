"""HTTP views for the Fitness Hub chatbot.

Provides a full-page chat (`/chatbot/`) and a JSON API endpoint
(`/chatbot/api/`) used by both the full page and the floating widget.
"""

import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import ChatSession, ChatMessage
from . import responder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(request) -> ChatSession:
    """Return the user’s current chat session, creating it if needed."""
    user = request.user if request.user.is_authenticated else None
    if user is not None:
        session, _ = ChatSession.objects.get_or_create(user=user)
        return session

    # Anonymous: pin to a session_key.
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
    return render(request, 'chatbot/chat.html', {
        'session': session,
        'recent': recent,
    })


@require_POST
def chat_api(request):
    """Accept JSON `{message: "..."}` and return JSON `{reply, intent, refused, reason, suggestions}`."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest('invalid json')

    text = (payload.get('message') or '').strip()
    session = _get_or_create_session(request)

    # Log the user message
    if text:
        ChatMessage.objects.create(session=session, role='user', content=text)

    result = responder.respond(text, user=request.user)

    # Log the bot reply (skip if empty input and a refusal went through)
    ChatMessage.objects.create(
        session=session,
        role='bot',
        content=result['reply'],
        intent=result['intent'],
    )

    suggestions = _suggestions_for(result['intent'])

    return JsonResponse({
        'reply': result['reply'],
        'intent': result['intent'],
        'refused': result['refused'],
        'reason': result['reason'],
        'suggestions': suggestions,
    })


def _suggestions_for(intent_name: str) -> list:
    """Return 3 quick-reply chip strings for a given intent."""
    table = {
        'greeting': [
            'Recommend an exercise for me',
            'How do I use the app?',
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
        'progress_help': [
            'Where is the Records page?',
            'What does the Progress page show?',
            'How do streaks work?',
        ],
        'default': [
            'Recommend an exercise',
            'How do I use the app?',
            'How much protein do I need?',
        ],
    }
    return table.get(intent_name, table['default'])
