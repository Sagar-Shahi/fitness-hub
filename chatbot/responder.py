"""Response generator: intent + knowledge + safety → user-facing reply."""

from . import intent, knowledge, safety


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_exercise_line(ex) -> str:
    """Format a single exercise as a compact one-liner."""
    parts = [f"**{ex.name}**"]
    if ex.category:
        parts.append(f"({ex.get_category_display()})")
    if ex.difficulty:
        parts.append(f"· {ex.get_difficulty_display()}")
    if ex.equipment:
        parts.append(f"· {ex.equipment}")
    return ' '.join(parts)


def _exercise_recommendation_reply(user, n: int = 4) -> str:
    """Pick exercises based on user's active goal if logged in, else general."""
    from exercises.models import Exercise
    goal = 'general'
    if user is not None and getattr(user, 'is_authenticated', False):
        profile = getattr(user, 'profile', None)
        if profile and profile.selected_goal:
            goal = profile.selected_goal

    pool = list(Exercise.objects.filter(goal=goal))
    if not pool:
        pool = list(Exercise.objects.all())
    pool = pool[:n]
    if not pool:
        return "The exercise library is empty right now. Try again in a moment."

    goal_desc = knowledge.GOAL_DESCRIPTIONS.get(goal, 'your goal')
    lines = ["Here are some exercises that fit your active goal — " + goal_desc + ":"]
    for ex in pool:
        lines.append(f"• {_fmt_exercise_line(ex)}")
    lines.append(
        "\nOpen the Workout Library to see all of them and mark them complete as you go."
    )
    return '\n'.join(lines)


def _category_exercises_reply(text: str) -> str:
    """Find a category in the user text and list its exercises."""
    text_l = text.lower()
    for cat, desc in knowledge.CATEGORY_DESCRIPTIONS.items():
        if cat in text_l:
            exs = knowledge.list_exercises_by_category(cat)
            if not exs:
                return f"No exercises found in the {cat.title()} category yet."
            lines = [f"**{cat.title()} exercises** — {desc}", ""]
            for ex in exs:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            return '\n'.join(lines)
    return "Tell me a muscle group (chest, back, shoulders, arms, legs, core, or cardio) and I'll list those exercises."


def _goal_exercises_reply(text: str) -> str:
    text_l = text.lower()
    for goal, desc in knowledge.GOAL_DESCRIPTIONS.items():
        if goal.replace('_', ' ') in text_l or goal in text_l:
            exs = knowledge.list_exercises_by_goal(goal)
            if not exs:
                return f"No exercises match the {goal} goal yet."
            lines = [f"**Exercises for {goal.replace('_', ' ').title()}** — {desc}", ""]
            for ex in exs:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            return '\n'.join(lines)
    return "Pick a goal: strength, hypertrophy, endurance, mobility, flexibility, or weight loss."


def _difficulty_exercises_reply(text: str) -> str:
    text_l = text.lower()
    for diff in ('beginner', 'intermediate', 'advanced'):
        if diff in text_l:
            exs = knowledge.list_exercises_by_difficulty(diff)
            if not exs:
                return f"No {diff} exercises yet."
            lines = [f"**{diff.title()} exercises** — {knowledge.DIFFICULTY_DESCRIPTIONS[diff]}", ""]
            for ex in exs:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            return '\n'.join(lines)
    return "Tell me a difficulty: beginner, intermediate, or advanced."


def _exercise_info_reply(text: str) -> str:
    from exercises.models import Exercise
    found = knowledge.search_exercises(text, limit=1)
    if not found:
        return (
            "I couldn’t find that exercise in the library. Browse the Workout Library "
            "or ask about a muscle group (e.g. “chest exercises”)."
        )
    ex = found[0]
    lines = [
        f"### {ex.name}",
        f"_{ex.get_category_display()} · {ex.get_difficulty_display()}_",
        "",
        ex.description or "No description on file yet.",
    ]
    if ex.target_muscles:
        lines += ["", f"**Targets:** {ex.target_muscles}"]
    if ex.equipment:
        lines += ["", f"**Equipment:** {ex.equipment}"]
    if ex.default_sets and ex.default_reps:
        lines += ["", f"**Working sets:** {ex.default_sets} × {ex.default_reps} reps"]
    if ex.duration_min:
        lines += [f"**Duration:** ~{ex.duration_min} min"]
    if ex.form_tips:
        lines += ["", "**Form tips:**", ex.form_tips]
    if ex.common_mistakes:
        lines += ["", "**Common mistakes:**", ex.common_mistakes]
    if ex.breathing:
        lines += ["", "**Breathing:**", ex.breathing]
    if ex.safety:
        lines += ["", f"**Safety:** {ex.safety}"]
    if ex.video_url:
        lines += ["", f"**Video:** {ex.video_url}"]
    return '\n'.join(lines)


def _app_help_reply(text: str, user) -> str:
    key, feat = knowledge.find_app_route_for_query(text)
    if feat:
        return (
            f"**{feat['title']}** — {feat['summary']}\n\n"
            f"Open it here: {feat['path']}"
        )
    # Generic app overview
    lines = [
        "Fitness Hub is built around six systems:",
        "• 🏋️ **Workouts** — 36 exercises ranked against your goal (/exercises/)",
        "• 📋 **Records** — auto-logged completions (/users/records/)",
        "• 📈 **Progress** — weekly volume, streaks, goal alignment (/progress/)",
        "• 🥗 **Diet** — clinical BMR/TDEE, food tracker, budget meals (/diet/)",
        "• 🛒 **Store** — outfits, gear, supplements (/store/)",
        "• 🔥 **Inspiration** — daily quote, 13 icons, training principles (/inspiration/)",
        "",
        "Ask me about any of these (e.g. “how do I change my password?”).",
    ]
    return '\n'.join(lines)


def _progress_help_reply(user) -> str:
    return (
        "**Tracking your workouts** is automatic:\n"
        "1. Open any exercise in the Workout Library.\n"
        "2. Hit **Mark Complete & Log** for a one-tap log, or **Log With Details** for reps/notes.\n"
        "3. Your entry appears in Records (grouped by day) and Progress (weekly volume + streaks).\n\n"
        "Want to change your goal? Go to Goals → New Goal, or open Settings → Change Goal."
    )


def _diet_app_help_reply() -> str:
    return (
        "**Diet Planner** (/diet/) shows your BMR, TDEE, and daily macro targets based on your "
        "body stats and active goal. From there you can:\n"
        "• **Plan** — view your full macros and food suggestions\n"
        "• **Foods** — click foods to build a meal and see live macro totals\n"
        "• **Budget** — pre-planned affordable meals\n"
        "• **Add Record** — log what you actually ate that day"
    )


def _settings_help_reply(text: str) -> str:
    t = text.lower()
    if 'password' in t:
        return (
            "**Change your password:** Settings → Password & security → Change password. "
            "Enter your current password, then the new one twice. You’ll stay signed in."
        )
    if 'username' in t:
        return (
            "**Change your username:** Settings → Account details → Account settings. "
            "Update the Username field and save. The new name must be unique."
        )
    if 'email' in t:
        return (
            "**Change your email:** Settings → Account details → Account settings. "
            "Update the Email field. We use it to recover your password."
        )
    return (
        "Settings hub: /users/settings/\n"
        "• Account details — username, name, email\n"
        "• Password & security — change your password\n"
        "• Fitness profile — age, height, weight, body type, goal"
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def respond(user_input: str, user=None) -> dict:
    """Return {'reply': str, 'intent': str, 'refused': bool, 'reason': str}."""
    if not user_input or not user_input.strip():
        return {
            'reply': safety.safety_refusal('empty'),
            'intent': 'empty',
            'refused': True,
            'reason': 'empty',
        }

    # 1. Safety first.
    safety_check = safety.check_user_input(user_input)
    if not safety_check['safe']:
        return {
            'reply': safety.safety_refusal(safety_check['reason']),
            'intent': 'safety',
            'refused': True,
            'reason': safety_check['reason'],
        }

    # 2. Scope check.
    if not safety.is_in_scope(user_input):
        return {
            'reply': safety.safety_refusal('off_topic'),
            'intent': 'off_topic',
            'refused': True,
            'reason': 'off_topic',
        }

    # 3. Classify intent.
    intent_name = intent.classify(user_input)
    text = user_input.strip()
    text_l = text.lower()

    # 4. Generate reply per intent.
    reply = ''
    if intent_name == intent.INTENT_GREETING:
        who = ''
        if user and getattr(user, 'is_authenticated', False):
            who = f", {user.first_name or user.username}"
        reply = (
            f"Hey{who}! 👋 I’m the Fitness Hub coach. I can help with exercises, "
            "app features, and general fitness & nutrition. What are you working on today?"
        )
    elif intent_name == intent.INTENT_GOODBYE:
        reply = "Take care. Log your workout before you go — it only takes a second. 💪"
    elif intent_name == intent.INTENT_THANKS:
        reply = "Anytime. Now go do the work — that’s where the results come from."
    elif intent_name == intent.INTENT_CATEGORY_EXERCISES:
        reply = _category_exercises_reply(text)
    elif intent_name == intent.INTENT_DIFFICULTY_EXERCISES:
        reply = _difficulty_exercises_reply(text)
    elif intent_name == intent.INTENT_GOAL_EXERCISES:
        reply = _goal_exercises_reply(text)
    elif intent_name == intent.INTENT_EXERCISE_RECOMMEND:
        reply = _exercise_recommendation_reply(user, n=4)
    elif intent_name == intent.INTENT_EXERCISE_INFO:
        reply = _exercise_info_reply(text)
    elif intent_name == intent.INTENT_NUTRITION:
        faq = knowledge.find_faq_answer(text)
        if faq:
            reply = safety.add_disclaimer_if_health(faq)
        else:
            reply = (
                "I can help with calories, protein, meal timing, and supplement basics. "
                "Try asking “how much protein should I eat?” or “what should I eat "
                "before a workout?”."
            )
    elif intent_name == intent.INTENT_DIET_APP_HELP:
        reply = _diet_app_help_reply()
    elif intent_name == intent.INTENT_PROGRESS_HELP:
        reply = _progress_help_reply(user)
    elif intent_name == intent.INTENT_APP_HELP:
        if 'password' in text_l or 'change' in text_l or 'username' in text_l or 'email' in text_l:
            # Settings-related questions get a direct settings answer.
            if any(kw in text_l for kw in ('password', 'username', 'email', 'change', 'security')):
                reply = _settings_help_reply(text)
            else:
                reply = _app_help_reply(text, user)
        else:
            reply = _app_help_reply(text, user)
    elif intent_name == intent.INTENT_GOAL_ADVICE:
        reply = (
            "Pick a clear goal and the rest of the app will tune itself to it. "
            "Open **Goals** (/goals/) → New Goal. Common goals:\n"
            "• **Build muscle** — hypertrophy workouts, slight calorie surplus, high protein\n"
            "• **Lose fat** — moderate calorie deficit, high protein, mix of strength + cardio\n"
            "• **Get strong** — strength-focused program, lower reps, longer recovery\n"
            "• **Get more mobile** — mobility + flexibility work, daily short sessions\n\n"
            "Your choice flows into the Workout Library recommendations and your Diet targets."
        )
    elif intent_name == intent.INTENT_RECOVERY:
        reply = safety.add_disclaimer_if_health(
            "**Recovery basics:**\n"
            "• Sleep 7–9 hours — this is where you actually adapt.\n"
            "• Walk 20–30 minutes on rest days to keep blood flowing.\n"
            "• Eat enough protein (1.6–2.2 g/kg/day) and total calories.\n"
            "• Soreness 24–72h after a session is normal; sharp pain during a lift is not — stop.\n"
            "• If something hurts for more than a few days, see a physio or doctor."
        )
    elif intent_name == intent.INTENT_WARMUP:
        reply = (
            "**Warm-up (5–10 min):**\n"
            "1. 3–5 min of easy cardio (bike, jump rope, brisk walk) to raise body temperature.\n"
            "2. Dynamic mobility for the joints you’ll use (arm circles, hip openers, bodyweight squats).\n"
            "3. 1–2 ramp-up sets of the exercise you’re about to do, building to your working weight.\n\n"
            "Skipping the warm-up is the #1 way people tweak something in the first set."
        )
    elif intent_name == intent.INTENT_GENERAL_FITNESS:
        faq = knowledge.find_faq_answer(text)
        reply = faq or (
            "For general training questions, the short answer is: be consistent, train "
            "each muscle 2x per week when you can, sleep well, and eat enough protein. "
            "Ask me something more specific — like “how often should I train?” or "
            "“how long should a workout be?”."
        )
    else:
        # Fallback: see if the FAQ still has a hit, or see if they’re asking about an app feature.
        faq = knowledge.find_faq_answer(text)
        if faq:
            reply = safety.add_disclaimer_if_health(faq)
            return {'reply': reply, 'intent': 'faq', 'refused': False, 'reason': ''}

        # Last try: search exercises by free text.
        matches = knowledge.search_exercises(text, limit=3)
        if matches:
            lines = ["I couldn’t find an exact answer, but here are some related exercises:"]
            for ex in matches:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            reply = '\n'.join(lines)
        else:
            reply = (
                "I’m not sure what you’re after. I can help with:\n"
                "• Exercise technique, form, and programming\n"
                "• Diet & nutrition basics\n"
                "• How to use any part of the app\n"
                "• Recovery, warm-up, training frequency\n\n"
                "Try rephrasing — for example “how do I do a push-up?” or “how do I change my password?”."
            )

    # Final sanity pass on the response.
    reply = safety.sanitize_output(reply)
    return {'reply': reply, 'intent': intent_name, 'refused': False, 'reason': ''}
