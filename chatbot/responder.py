"""Responder — intent + knowledge + context + persona → reply.

Pipeline:
  1. Sanity check input.
  2. Safety filter (input).
  3. Scope filter.
  4. Classify intent.
  5. Build user context (streak, goal, last workout).
  6. Generate reply per intent, with persona wrappers.
  7. Add medical disclaimer if the reply is health-related.
  8. Enforce persona guidelines (scrub forbidden phrases).
  9. Final sanitize_output.
"""

from . import (
    coach_context,
    guidelines,
    intent,
    knowledge,
    personality,
    safety,
)


# ---------------------------------------------------------------------------
# Exercise formatting helpers
# ---------------------------------------------------------------------------

def _fmt_exercise_line(ex) -> str:
    parts = [f"**{ex.name}**"]
    if ex.category:
        parts.append(f"({ex.get_category_display()})")
    if ex.difficulty:
        parts.append(f"· {ex.get_difficulty_display()}")
    if ex.equipment:
        parts.append(f"· {ex.equipment}")
    return ' '.join(parts)


def _exercise_recommendation_reply(user, n: int = 4) -> str:
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
    lines = [f"Here are some exercises that fit your active goal — {goal_desc}:"]
    for ex in pool:
        lines.append(f"• {_fmt_exercise_line(ex)}")
    lines.append("\nOpen the Workout Library to see all of them and mark them complete as you go.")
    lines.append(f"Log in at `/exercises/` and let's get moving.")
    return '\n'.join(lines)


def _category_exercises_reply(text: str) -> str:
    text_l = text.lower()
    for cat, desc in knowledge.CATEGORY_DESCRIPTIONS.items():
        if cat in text_l:
            exs = knowledge.list_exercises_by_category(cat)
            if not exs:
                return f"No exercises found in the {cat.title()} category yet."
            lines = [f"**{cat.title()} exercises** — {desc}", ""]
            for ex in exs:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            lines.append(f"\nFull list and details: `/exercises/`.")
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
            "I couldn't find that exercise in the library. Browse the Workout Library "
            "(`/exercises/`) or ask about a muscle group (e.g. “chest exercises”)."
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
    lines.append(f"\nOpen it: `/exercises/{ex.slug}/`")
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# App-help replies
# ---------------------------------------------------------------------------

def _app_help_reply(text: str, user) -> str:
    key, feat = knowledge.find_app_route_for_query(text)
    if feat:
        return (
            f"**{feat['title']}** — {feat['summary']}\n\n"
            f"{feat.get('how', '')}\n\n"
            f"Open it: {feat['path']}"
        )
    # Generic app overview
    lines = [
        "Here's every part of Fitness Hub. I know all of them:",
        "• 🏋️ **Workout Library** (`/exercises/`) — 36 exercises ranked against your goal",
        "• 📋 **Records** (`/users/records/`) — every session you've logged, grouped by day",
        "• 📈 **Progress** (`/progress/`) — weekly volume, streaks, goal alignment",
        "• 🎯 **Goals** (`/goals/`) — your primary goal, drives recommendations",
        "• 🥗 **Diet** (`/diet/`) — BMR/TDEE, food tracker, budget meals",
        "• 🛒 **Store** (`/store/`) — gear, outfits, supplements; cart & orders included",
        "• 🎮 **Play** (`/play/`) — XP, levels, badges, quests, leaderboard",
        "• 🔥 **Inspiration** (`/inspiration/`) — daily quote, 13 athlete profiles",
        "• ⚙️ **Settings** (`/users/settings/`) — username, password, body stats, goals",
        "• 👤 **Profile** (`/users/profile/`) — read-only summary of your account",
        "",
        "Ask me “how do I log a workout?” or “how do I change my password?” and I'll walk you through it step by step.",
    ]
    return '\n'.join(lines)


def _deep_app_help_reply(text: str) -> str:
    answer = knowledge.find_howto(text)
    if answer:
        return answer
    # Fall through to feature route.
    key, feat = knowledge.find_app_route_for_query(text)
    if feat:
        return f"**{feat['title']}** — {feat['summary']}\n\n{feat.get('how', '')}\n\nOpen it: {feat['path']}"
    return _app_help_reply(text, user=None)


def _settings_help_reply(text: str) -> str:
    t = text.lower()
    if 'password' in t:
        return (
            "**Change your password:** Settings → Password & security → Change password "
            "(`/users/settings/password/`). Enter your current password, then the new one "
            "twice. You'll stay signed in."
        )
    if 'username' in t:
        return (
            "**Change your username:** Settings → Account details → Account settings "
            "(`/users/settings/account/`). Update the Username field and save. The new "
            "name must be unique."
        )
    if 'email' in t:
        return (
            "**Change your email:** Settings → Account details → Account settings "
            "(`/users/settings/account/`). Update the Email field. We use it to recover "
            "your password."
        )
    return (
        "Settings hub: `/users/settings/`\n"
        "• **Account details** (`/users/settings/account/`) — username, name, email\n"
        "• **Password & security** (`/users/settings/password/`) — change your password\n"
        "• **Fitness profile** — age, height (ft), weight (kg), body type, goal"
    )


def _progress_help_reply(user, ctx: dict | None = None) -> str:
    lines = [
        "**Tracking your workouts** is automatic:",
        "1. Open any exercise in the Workout Library (`/exercises/`).",
        "2. Hit **Mark Complete & Log** for a one-tap log, or **Log With Details** for reps/notes.",
        "3. Your entry appears in **Records** (`/users/records/`) and **Progress** (`/progress/`).",
    ]
    if ctx and ctx.get('streak_days', 0) >= 1:
        lines.append(f"\nYou're on a **{ctx['streak_days']}-day streak** right now. Keep it going.")
    if ctx and ctx.get('days_since_last') is not None and ctx['days_since_last'] >= 1:
        lines.append(f"Last session was {ctx['days_since_last']} day(s) ago.")
    return '\n'.join(lines)


def _diet_app_help_reply() -> str:
    return (
        "**Diet Planner** (`/diet/`) shows your BMR, TDEE, and daily macro targets based on your "
        "body stats and active goal. From there you can:\n"
        "• **Suggest** (`/diet/suggest/`) — your full plan with food suggestions\n"
        "• **Foods** (`/diet/foods/`) — click foods to build a meal, totals update live\n"
        "• **Budget Meals** (`/diet/budget-meals/`) — pre-planned affordable meals\n"
        "• **Add Record** (`/diet/create/`) — log what you actually ate"
    )


# ---------------------------------------------------------------------------
# New intent handlers (motivation / where_am_i / who / next_step)
# ---------------------------------------------------------------------------

def _motivation_reply(text: str, ctx: dict) -> str:
    """Personalized motivation based on user state."""
    text_l = text.lower()
    # If user just wants to talk / vent, be a listening ear
    if any(kw in text_l for kw in ('just need to talk', 'need someone to talk', 'can we talk', 'talk to me', 'listen')):
        return (
            "I'm here. You can talk to me about anything — how your day's going, "
            "what's on your mind, whatever. Sometimes just saying it out loud helps. "
            "I'll listen."
        )
    base = coach_context.motivation_for_context(ctx)
    streak = ctx.get('streak_days', 0)
    days_off = ctx.get('days_since_last') or 0

    # Add a personalized touch
    extras = []
    if days_off >= 3:
        extras.append(personality.soft_sarcasm(days_off))
    elif streak >= 3:
        extras.append(personality.warm_encouragement(streak))

    if extras:
        base = f"{base}\n\n_{extras[0]}_"

    # Always close with a warm closer
    base += f"\n\n{personality.bot_closer()}"
    return base


def _where_am_i_reply(ctx: dict) -> str:
    """Reply for new users / 'where do I start'."""
    if ctx and ctx.get('has_active_goal') and not ctx.get('is_new'):
        return (
            "You've already got a goal set and some sessions logged — you're not really "
            "new anymore. If you want a refresher, ask me 'what should I do next' and I'll "
            "give you a targeted suggestion. Otherwise, just open `/exercises/` and pick "
            "something that looks fun."
        )
    return (
        "Welcome to Fitness Hub. Here's the 60-second tour:\n"
        "1. **Set a goal** at `/goals/` — strength, hypertrophy, endurance, mobility, "
        "flexibility, or weight loss. The whole app tunes to this.\n"
        "2. **Pick a workout** at `/exercises/`. Filter by muscle group or your active goal.\n"
        "3. **Log it** with the **Mark Complete** button. The entry shows up in Records and Progress.\n"
        "4. **Eat smart** at `/diet/` — BMR, TDEE, macros, food tracker, budget meals.\n"
        "5. **Stay motivated** at `/inspiration/` — daily quote and athlete profiles.\n\n"
        "That's the whole loop. Pick any step and start there. Or just ask me for a "
        "specific suggestion."
    )


def _next_step_reply(ctx: dict) -> str:
    """Reply for 'what should I do' / 'what next'."""
    base = coach_context.next_action_for_context(ctx)
    if ctx and not ctx.get('is_new'):
        base += f"\n\n{personality.warm_encouragement(ctx.get('streak_days', 0))}"
    else:
        base += f"\n\n{personality.bot_closer()}"
    return base


def _who_are_you_reply() -> str:
    return (
        f"{personality.identity_line()}\n\n"
        "Here's what I can help with:\n"
        "• Exercise technique, form cues, programming, warm-up, and recovery\n"
        "• Cardio types (HIIT, LISS, zone training, running tips)\n"
        "• Mobility, stretching, and cool-down routines\n"
        "• Diet, nutrition basics, and evidence-based legal supplements (creatine, whey, "
        "caffeine, vitamins)\n"
        "• Sleep and recovery for active people\n"
        "• Every page and feature in Fitness Hub — workouts, records, progress, goals, "
        "diet, store, cart, orders, settings, profile, inspiration\n"
        "• Motivation, when you need a push (or a thoughtful reminder)\n\n"
        f"I'm not a doctor, not a dietitian, not a personal trainer, and I never modify your "
        f"account data — I'm read-only. For medical issues, please see a qualified "
        f"professional."
    )


# ---------------------------------------------------------------------------
# Knowledge intent handlers (programming, cardio, mobility, supplements, sleep)
# ---------------------------------------------------------------------------

def _knowledge_reply(text: str) -> str | None:
    """Pull a knowledge base answer that includes the new sources.

    Tries: principles → cardio → mobility → sleep → supplements → FAQ → how-to.
    Returns the first match, or None.
    """
    if not text:
        return None
    for finder in (
        knowledge.find_principle,
        knowledge.find_cardio_answer,
        knowledge.find_mobility_answer,
        knowledge.find_sleep_recovery_answer,
        knowledge.find_supplement_answer,
        knowledge.find_faq_answer,
        knowledge.find_howto,
    ):
        result = finder(text)
        if result:
            return result
    return None


def _programming_reply(text: str) -> str:
    base = knowledge.find_principle(text) or (
        "**Programming basics, the short version:**\n"
        "• Train each muscle 2x/week, 10–20 hard sets per muscle per week.\n"
        "• Rep ranges: 1–5 strength, 6–12 hypertrophy, 12–20 endurance.\n"
        "• Add weight or reps gradually (progressive overload).\n"
        "• Take a deload every 4–6 weeks (drop volume 40–50%).\n"
        "• Sleep and eat enough — that's where the adaptation happens."
    )
    return f"{personality.sharp_question_line()}\n\n{base}\n\n{personality.bot_closer()}"


def _cardio_reply(text: str) -> str:
    base = knowledge.find_cardio_answer(text) or (
        "**Cardio, the short version:**\n"
        "• **LISS (Zone 2):** easy pace, 30–60 min, 2–4x/week. Builds the aerobic base.\n"
        "• **HIIT:** 20–60 sec hard, equal rest, 15–25 min total. 1–3x/week max.\n"
        "• **Pick a mode you like** — running, biking, rowing, jump rope, swimming.\n"
        "• Warm up 5 min easy, work, cool down 5 min easy.\n\n"
        "Mix both styles. The boring zone 2 is what most people should be doing more of."
    )
    return f"{base}\n\n{personality.technique_closer()}"


def _mobility_reply(text: str) -> str:
    base = knowledge.find_mobility_answer(text) or (
        "**Mobility in 5 minutes a day:**\n"
        "• **Hips:** 90/90 rotations, deep squat hold, couch stretch.\n"
        "• **Shoulders:** wall slides, dead hangs, thoracic rotations.\n"
        "• **Thoracic spine:** cat-cow, open-book stretch, foam roller extensions.\n"
        "• **Ankles:** calf stretches, ankle circles — important for squat depth.\n\n"
        "Consistency beats intensity. A 5-min daily flow beats a 30-min monthly one."
    )
    return f"{base}\n\n{personality.technique_closer()}"


def _supplements_reply(text: str) -> str:
    base = knowledge.find_supplement_answer(text) or (
        "**The legal, evidence-based shortlist:**\n"
        "1. **Creatine monohydrate** — 3–5 g/day. Cheap. Effective. Safe.\n"
        "2. **Vitamin D** — 1000–2000 IU/day, especially with limited sun.\n"
        "3. **Whey or any protein** — to hit your daily protein target.\n"
        "4. **Caffeine** — 3–6 mg/kg, ~30–60 min pre-workout.\n"
        "5. **Magnesium** — 200–400 mg before bed, helps sleep and recovery.\n\n"
        "That's it. Everything else is bonus."
    )
    return safety.add_disclaimer_if_health(
        f"{personality.sharp_question_line()}\n\n{base}\n\n{personality.bot_closer()}"
    )


def _sleep_recovery_reply(text: str) -> str:
    base = knowledge.find_sleep_recovery_answer(text) or (
        "**Recovery cheat sheet:**\n"
        "• **Sleep 7–9 hours.** This is where the adaptation happens.\n"
        "• **Active rest on off days:** 20–30 min walk, mobility, or easy bike.\n"
        "• **Eat at maintenance** — don't under-eat on rest days.\n"
        "• **Hydrate:** pale yellow urine is the goal.\n"
        "• **Deload every 4–6 weeks** if you're training hard."
    )
    return f"{base}\n\n{personality.bot_closer()}"


# ---------------------------------------------------------------------------
# Reply wrapping (persona)
# ---------------------------------------------------------------------------

def _wrap_with_persona(reply: str, ctx: dict | None, intent_name: str) -> str:
    """Optionally prefix or suffix the reply to match the bot voice.

    For long informational replies we don't add anything (the user is here
    for info). For short replies or motivational intents we add a tone touch.
    """
    if intent_name in (intent.INTENT_GREETING, intent.INTENT_MOTIVATION, intent.INTENT_NEXT_STEP,
                       intent.INTENT_WHERE_AM_I, intent.INTENT_GOODBYE):
        return reply  # those already carry persona
    return reply


# ---------------------------------------------------------------------------
# Gamification / "Play" handlers
# ---------------------------------------------------------------------------

def _get_gamification_summary(user) -> dict | None:
    """Return gamification summary dict for the user, or None when not authed
    or the gamification app is not installed.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        from gamification.services import get_player_summary
    except Exception:
        return None
    try:
        return get_player_summary(user)
    except Exception:
        return None


def _play_status_reply(user) -> str:
    summary = _get_gamification_summary(user)
    if not summary:
        return (
            "I'd love to talk levels and XP, but you need to be signed in first. "
            "Create an account (or log in) and the play system will start tracking "
            "your workouts, goals, meals, and orders."
        )
    level = summary.get('level', 1)
    xp = summary.get('xp', 0)
    title = summary.get('title', 'Rookie')
    coins = summary.get('coins', 0)
    shields = summary.get('streak_shields', 0)
    into = summary.get('xp_into_level', 0)
    to_next = summary.get('xp_to_next_level', 100)
    recent = summary.get('recent_badges', []) or []

    lines = [
        f"You're **Level {level}** — *{title}*. Current XP: ⚡ {xp}.",
        f"Progress to Level {level + 1}: {into} / {to_next} XP.",
    ]
    extras = []
    if coins:
        extras.append(f"🪙 {coins} coins")
    if shields:
        extras.append(f"🛡️ {shields} streak shields")
    if extras:
        lines.append("Pocket: " + " · ".join(extras))
    if recent:
        names = ", ".join(getattr(ub.badge, 'name', str(ub)) for ub in recent[:3])
        lines.append(f"Recent badges: {names}.")
    lines.append("\nOpen your full Player Hub at `/play/`.")
    return '\n'.join(lines)


def _play_help_reply(user) -> str:
    summary = _get_gamification_summary(user)
    if not summary:
        return (
            "The play system tracks XP, levels, badges, and quests for every signed-in "
            "member. After you log in, the nav shows your current level and a small XP bar. "
            "Sign in or create an account to get started."
        )
    daily = summary.get('daily_quests', []) or []
    if daily:
        quest_lines = ["Here are today's quests:"]
        for uq in daily[:3]:
            quest_lines.append(
                f"• {uq.quest.icon} **{uq.quest.name}** — {uq.progress}/{uq.target} "
                f"(+{uq.quest.xp_reward} XP)"
            )
        quest_block = "\n".join(quest_lines)
    else:
        quest_block = "No active daily quests right now — re-roll on the Quest Board to get a fresh set."

    return (
        f"**How the play system works:**\n"
        f"• Earn XP by logging workouts, finishing goals, logging meals, and buying gear from the store.\n"
        f"• XP grows your **level and title** — Rookie → Beast → Immortal → Transcendent.\n"
        f"• Hit thresholds to **unlock badges** (First Step, Week Warrior, Iron Month, etc.).\n"
        f"• Daily and weekly **quests** give bonus XP and coins.\n"
        f"• **Streak shields** protect your workout streak when life gets in the way.\n\n"
        f"{quest_block}\n\n"
        f"Browse everything at `/play/` — Player Hub, Badges, Quests, and Leaderboard."
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def respond(user_input: str, user=None) -> dict:
    """Return {'reply': str, 'intent': str, 'refused': bool, 'reason': str}."""
    # 1. Empty input
    if not user_input or not user_input.strip():
        return {
            'reply': safety.safety_refusal('empty'),
            'intent': 'empty',
            'refused': True,
            'reason': 'empty',
        }

    # 2. Safety
    safety_check = safety.check_user_input(user_input)
    if not safety_check['safe']:
        return {
            'reply': safety.safety_refusal(safety_check['reason']),
            'intent': 'safety',
            'refused': True,
            'reason': safety_check['reason'],
        }

    # 3. Scope
    if not safety.is_in_scope(user_input):
        return {
            'reply': safety.safety_refusal('off_topic'),
            'intent': 'off_topic',
            'refused': True,
            'reason': 'off_topic',
        }

    # 4. Classify
    intent_name = intent.classify(user_input)
    text = user_input.strip()
    text_l = text.lower()

    # 5. Build user context
    ctx = coach_context.build_user_context(user)
    ctx = coach_context.hydrate_goal_label(ctx)

    # 6. Generate reply per intent
    reply = ''
    if intent_name == intent.INTENT_WHO_ARE_YOU:
        reply = _who_are_you_reply()
    elif intent_name == intent.INTENT_GREETING:
        reply = coach_context.greeting_for_context(ctx)
    elif intent_name == intent.INTENT_GOODBYE:
        streak = ctx.get('streak_days', 0) if ctx else 0
        if streak >= 1:
            reply = (
                f"Catch you later. Don't break the {streak}-day streak — it's "
                f"the most valuable thing in your account. See you soon."
            )
        else:
            reply = "Take care. Log your workout before you go — it only takes a second. 💪"
    elif intent_name == intent.INTENT_THANKS:
        reply = "Anytime. Now go do the work — that's where the results come from."
    elif intent_name == intent.INTENT_MOTIVATION:
        reply = _motivation_reply(text, ctx)
    elif intent_name == intent.INTENT_NEXT_STEP:
        reply = _next_step_reply(ctx)
    elif intent_name == intent.INTENT_WHERE_AM_I:
        reply = _where_am_i_reply(ctx)
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
        # First try the new supplement / sleep / FAQ sources so users get
        # the deepest answer possible.
        sup = knowledge.find_supplement_answer(text)
        if sup:
            reply = safety.add_disclaimer_if_health(sup)
        else:
            faq = knowledge.find_faq_answer(text)
            if faq:
                reply = safety.add_disclaimer_if_health(faq)
            else:
                reply = (
                    "I can help with calories, protein, meal timing, and supplement basics. "
                    "Try asking “how much protein should I eat?” or “what should I eat "
                    "before a workout?”."
                )
    elif intent_name == intent.INTENT_PROGRAMMING:
        reply = _programming_reply(text)
    elif intent_name == intent.INTENT_CARDIO:
        reply = _cardio_reply(text)
    elif intent_name == intent.INTENT_MOBILITY:
        reply = _mobility_reply(text)
    elif intent_name == intent.INTENT_SUPPLEMENTS:
        reply = _supplements_reply(text)
    elif intent_name == intent.INTENT_SLEEP:
        reply = _sleep_recovery_reply(text)
    elif intent_name == intent.INTENT_DIET_APP_HELP:
        reply = _diet_app_help_reply()
    elif intent_name == intent.INTENT_PROGRESS_HELP:
        reply = _progress_help_reply(user, ctx)
    elif intent_name == intent.INTENT_DEEP_APP_HELP:
        reply = _deep_app_help_reply(text)
    elif intent_name == intent.INTENT_APP_HELP:
        if any(kw in text_l for kw in ('password', 'username', 'email', 'security', 'change password', 'change username', 'change email')):
            reply = _settings_help_reply(text)
        else:
            reply = _app_help_reply(text, user)
    elif intent_name == intent.INTENT_GOAL_ADVICE:
        reply = (
            "Pick a clear goal and the rest of the app will tune itself to it. "
            "Open **Goals** (`/goals/`) → pick one. Common goals:\n"
            "• **Build muscle** — hypertrophy workouts, slight calorie surplus, high protein\n"
            "• **Lose fat** — moderate calorie deficit, high protein, mix of strength + cardio\n"
            "• **Get strong** — strength-focused program, lower reps, longer recovery\n"
            "• **Get more mobile** — mobility + flexibility work, daily short sessions\n\n"
            "Your choice flows into the Workout Library recommendations and your Diet targets."
        )
    elif intent_name == intent.INTENT_RECOVERY:
        # Try the deeper recovery / sleep / soreness knowledge first.
        deep = _knowledge_reply(text)
        if deep:
            reply = safety.add_disclaimer_if_health(deep)
        else:
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
            "2. Dynamic mobility for the joints you'll use (arm circles, hip openers, bodyweight squats).\n"
            "3. 1–2 ramp-up sets of the exercise you're about to do, building to your working weight.\n\n"
            "Skipping the warm-up is the #1 way people tweak something in the first set."
        )
    elif intent_name == intent.INTENT_PLAY_STATUS:
        reply = _play_status_reply(user)
    elif intent_name == intent.INTENT_PLAY_HELP:
        reply = _play_help_reply(user)
    elif intent_name == intent.INTENT_GENERAL_FITNESS:
        faq = knowledge.find_faq_answer(text)
        reply = faq or (
            "For general training questions, the short answer is: be consistent, train "
            "each muscle 2x per week when you can, sleep well, and eat enough protein. "
            "Ask me something more specific — like “how often should I train?” or "
            "“how long should a workout be?”."
        )
    else:
        # Fallback: try every knowledge source, then app route, then search.
        deep = _knowledge_reply(text)
        if deep:
            return {
                'reply': safety.add_disclaimer_if_health(deep),
                'intent': 'knowledge',
                'refused': False,
                'reason': '',
            }

        # Muscle-group encyclopedia (form cues, common mistakes)
        enc = knowledge.encyclopedia_reply(text)
        if enc:
            return {'reply': enc, 'intent': 'encyclopedia', 'refused': False, 'reason': ''}

        key, feat = knowledge.find_app_route_for_query(text)
        if feat:
            reply = (
                f"**{feat['title']}** — {feat['summary']}\n\n"
                f"{feat.get('how', '')}\n\n"
                f"Open it: {feat['path']}"
            )
            return {'reply': reply, 'intent': 'app_help', 'refused': False, 'reason': ''}

        matches = knowledge.search_exercises(text, limit=3)
        if matches:
            lines = ["I couldn't find an exact answer, but here are some related exercises:"]
            for ex in matches:
                lines.append(f"• {_fmt_exercise_line(ex)}")
            lines.append(f"\nOr open the Workout Library at `/exercises/`.")
            reply = '\n'.join(lines)
        else:
            # If the user is feeling emotional, don't dump a capabilities list
            emotion = personality.detect_emotion(user_input)
            if emotion:
                reply = (
                    "I'm here. You don't have to figure everything out right now. "
                    "Whenever you're ready, I can help with workouts, nutrition, "
                    "or anything in the app — no pressure at all."
                )
            else:
                reply = (
                    "I'm not sure what you're after. I can help with:\n"
                    "• Exercise technique, form cues, and programming (sets, reps, splits)\n"
                    "• Cardio (HIIT, LISS, zone training, running tips)\n"
                    "• Mobility, stretching, cool-downs\n"
                    "• Diet & nutrition basics, plus legal supplements\n"
                    "• Sleep and recovery\n"
                    "• How to use any part of the app — workouts, diet, store, play, etc.\n"
                    "• Gamification: XP, levels, badges, quests, leaderboards\n"
                    "• A motivational (or understanding) push when you need it\n\n"
                    "Try rephrasing — for example “how do I do a push-up?”, “what is RPE?”, "
                    "“how should I warm up?”, “what level am I?”, or “how do I change my password?”."
                )

    # 7. Disclaimer if the reply is health/nutrition related
    if intent_name in (intent.INTENT_NUTRITION, intent.INTENT_RECOVERY, intent.INTENT_GOAL_ADVICE,
                       intent.INTENT_GENERAL_FITNESS, intent.INTENT_SUPPLEMENTS,
                       intent.INTENT_SLEEP):
        reply = safety.add_disclaimer_if_health(reply)

    # 8. Enforce persona guidelines (scrub forbidden phrases)
    reply = guidelines.enforce_reply(reply)

    # 9. Wrap with emotional awareness (unless already refused)
    reply = personality.respond_to_emotion(reply, user_input)

    # 10. Final sanitize_output
    reply = safety.sanitize_output(reply)

    return {'reply': reply, 'intent': intent_name, 'refused': False, 'reason': ''}
