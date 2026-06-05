"""Rule-based intent classifier for the Fitness Hub chatbot.

Every pattern is a list of trigger phrases. The first match wins. If nothing
matches, the intent is `unknown` and the bot falls back to a generic
clarification or an out-of-scope refusal.
"""


INTENT_GREETING = 'greeting'
INTENT_GOODBYE = 'goodbye'
INTENT_THANKS = 'thanks'

INTENT_APP_HELP = 'app_help'
INTENT_EXERCISE_RECOMMEND = 'exercise_recommend'
INTENT_EXERCISE_INFO = 'exercise_info'
INTENT_CATEGORY_EXERCISES = 'category_exercises'
INTENT_GOAL_EXERCISES = 'goal_exercises'
INTENT_DIFFICULTY_EXERCISES = 'difficulty_exercises'
INTENT_NUTRITION = 'nutrition'
INTENT_GENERAL_FITNESS = 'general_fitness'
INTENT_DIET_APP_HELP = 'diet_app_help'
INTENT_PROGRESS_HELP = 'progress_help'
INTENT_GOAL_ADVICE = 'goal_advice'
INTENT_RECOVERY = 'recovery'
INTENT_WARMUP = 'warmup'
INTENT_FALLBACK = 'fallback'


INTENT_RULES = [
    (INTENT_GREETING, [
        'hi', 'hello', 'hey', 'yo', 'good morning', 'good afternoon',
        'good evening', 'howdy', 'greetings',
    ]),
    (INTENT_GOODBYE, [
        'bye', 'goodbye', 'see you', 'see ya', 'later', 'cya',
    ]),
    (INTENT_THANKS, [
        'thanks', 'thank you', 'ty', 'thx', 'appreciate it', 'cheers',
    ]),
    (INTENT_WARMUP, [
        'warm up', 'warmup', 'warm-up', 'how to warm', 'do i need to warm',
    ]),
    (INTENT_RECOVERY, [
        'recover', 'recovery', 'sore', 'soreness', 'doms', 'rest day',
        'i pulled', 'i hurt', 'injury', 'pain after', 'tendon',
    ]),
    (INTENT_CATEGORY_EXERCISES, [
        'chest exercise', 'back exercise', 'shoulder exercise', 'arm exercise',
        'leg exercise', 'core exercise', 'cardio exercise',
        'chest workout', 'back workout', 'shoulder workout', 'arm workout',
        'leg workout', 'core workout', 'cardio workout',
        'exercises for chest', 'exercises for back', 'exercises for legs',
        'exercises for arms', 'exercises for core', 'exercises for shoulders',
        'exercises for cardio',
    ]),
    (INTENT_DIFFICULTY_EXERCISES, [
        'beginner exercise', 'beginner workout', 'easy workout',
        'advanced exercise', 'advanced workout', 'hard workout',
        'intermediate exercise', 'intermediate workout',
    ]),
    (INTENT_GOAL_EXERCISES, [
        'strength exercise', 'hypertrophy exercise', 'endurance exercise',
        'mobility exercise', 'flexibility exercise', 'weight loss exercise',
        'exercises for strength', 'exercises for hypertrophy',
        'exercises for endurance', 'exercises for weight loss',
        'exercises for mobility', 'exercises for flexibility',
    ]),
    (INTENT_EXERCISE_RECOMMEND, [
        'recommend', 'recommendation', 'suggest', 'suggestion', 'what should i do',
        'what to do today', 'give me a workout', 'pick an exercise',
        'best exercise', 'top exercise', 'good exercise',
    ]),
    (INTENT_EXERCISE_INFO, [
        'how to do', 'how do i do', 'tell me about', 'explain',
        'what is a ', 'whats a ', "what's a ",
        'form for', 'technique for', 'tips for', 'cues for',
    ]),
    (INTENT_NUTRITION, [
        'how many calories', 'calorie', 'protein', 'macro', 'carbs', 'fat intake',
        'what to eat', 'should i eat', 'meal plan', 'pre workout', 'post workout',
        'creatine', 'supplement', 'whey', 'protein powder', 'water intake',
        'how much water', 'cheap meal', 'budget meal',
    ]),
    (INTENT_DIET_APP_HELP, [
        'diet planner', 'diet page', 'food tracker', 'budget meals page',
        'how to log food', 'how to log a meal',
    ]),
    (INTENT_PROGRESS_HELP, [
        'how to track', 'how to log a workout', 'how to mark complete',
        'workout records', 'records page', 'progress page',
        'track', 'tracking', 'streak', 'volume', 'progress',
    ]),
    (INTENT_APP_HELP, [
        'how do i use', 'how to use', 'where is', 'where do i find',
        'how to change', 'how to set', 'app', 'feature', 'features',
        'sign up', 'signup', 'register', 'login', 'log in',
        'change', 'settings', 'password', 'username', 'email',
    ]),
    (INTENT_GOAL_ADVICE, [
        'lose weight', 'gain weight', 'gain muscle', 'build muscle',
        'get strong', 'get stronger', 'get lean', 'cut', 'bulk',
        'recomp', 'fat loss', 'weight loss', 'muscle gain',
    ]),
    (INTENT_GENERAL_FITNESS, [
        'how often', 'how many days', 'how long should', 'should i do',
        'how much cardio', 'split', 'routine', 'program', 'frequency',
    ]),
]


def classify(text: str) -> str:
    """Return the first matching intent, or FALLBACK.

    Uses word-boundary matching so short phrases like "sup" don't accidentally
    match inside common words ("super").
    """
    import re

    if not text:
        return INTENT_FALLBACK
    t = text.lower().strip()
    tokens = re.findall(r"[a-z0-9'\-]+", t)
    token_set = set(tokens)

    for intent, phrases in INTENT_RULES:
        for phrase in phrases:
            p = phrase.strip().lower()
            # Multi-word phrase: substring search is fine.
            if ' ' in p:
                if p in t:
                    return intent
                continue
            # Single-word phrase: require it as its own token.
            p_norm = p.strip("'").strip('-')
            if p_norm and p_norm in token_set:
                return intent

    return INTENT_FALLBACK
