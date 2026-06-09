"""Rule-based intent classifier for the Fitness Hub chatbot.

Every pattern is a list of trigger phrases. The first match wins. If nothing
matches, the intent is `unknown` and the bot falls back to a generic
clarification or an out-of-scope refusal.
"""


INTENT_GREETING = 'greeting'
INTENT_GOODBYE = 'goodbye'
INTENT_THANKS = 'thanks'

INTENT_APP_HELP = 'app_help'
INTENT_DEEP_APP_HELP = 'deep_app_help'
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
INTENT_MOTIVATION = 'motivation'
INTENT_WHERE_AM_I = 'where_am_i'
INTENT_WHO_ARE_YOU = 'who_are_you'
INTENT_NEXT_STEP = 'next_step'
INTENT_PROGRAMMING = 'programming'
INTENT_CARDIO = 'cardio'
INTENT_MOBILITY = 'mobility'
INTENT_SUPPLEMENTS = 'supplements'
INTENT_SLEEP = 'sleep'
INTENT_PLAY_STATUS = 'play_status'
INTENT_PLAY_HELP = 'play_help'
INTENT_FALLBACK = 'fallback'


INTENT_RULES = [
    # --- Social block (always first) --------------------------------------
    (INTENT_GREETING, [
        'hi', 'hello', 'hey', 'yo', 'good morning', 'good afternoon',
        'good evening', 'howdy', 'greetings', 'sup',
        'नमस्ते', 'नमस्कार', 'हेलो', 'कस्तो छ', 'के हाल छ',
        'namaste', 'namaskar',
    ]),
    (INTENT_GOODBYE, [
        'bye', 'goodbye', 'see you', 'see ya', 'later', 'cya',
        'फेरि भेटौंला', 'बिदा', 'अलविदा', 'pheri betaula',
    ]),
    (INTENT_THANKS, [
        'thanks', 'thank you', 'ty', 'thx', 'appreciate it', 'cheers',
        'धन्यवाद', 'dherai dhanyabad', 'धेरै धन्यवाद',
    ]),
    (INTENT_WHO_ARE_YOU, [
        'who are you', 'what are you', 'are you ai', 'are you a bot',
        'are you human', 'are you real', 'your name', 'what is coach',
        'tell me about yourself',
        'तिमी को हौ', 'यो के हो', 'को हौ तिमी',
    ]),
    (INTENT_MOTIVATION, [
        'motivate me', 'motivation', 'i am lazy', "i'm lazy", 'i am tired',
        "i'm tired", 'no energy', 'no motivation', 'give up', 'i quit',
        "i don't want to", 'dont feel like', "don't feel like",
        'i skipped', 'i missed', 'i havent trained', "haven't trained",
        'cant be bothered', "can't be bothered", 'unmotivated', 'procrastinating',
        'i dont want to workout', 'do not want to train',
        'lazy', 'tired', 'exhausted', 'demotivated',
        'feel like quitting', 'want to give up',
        'just need to talk', 'need someone to talk', 'can we talk',
        'मलाई मोटिभेसन चाहियो', 'म अल्छी छु', 'म थाकेँ',
        'अल्छी', 'थकाइ लाग्यो', 'मोटिभेसन',
    ]),

    # --- Motivational block -----------------------------------------------
    (INTENT_MOTIVATION, [
        'motivate me', 'motivation', 'i am lazy', "i'm lazy", 'i am tired',
        "i'm tired", 'no energy', 'no motivation', 'give up', 'i quit',
        "i don't want to", 'dont feel like', "don't feel like",
        'i skipped', 'i missed', 'i havent trained', "haven't trained",
        'cant be bothered', "can't be bothered", 'unmotivated', 'procrastinating',
        'i dont want to workout', 'do not want to train',
        'lazy', 'tired', 'exhausted', 'demotivated',
        'feel like quitting', 'want to give up',
        'मलाई मोटिभेसन चाहियो', 'म अल्छी छु', 'म थाकेँ',
        'अल्छी', 'थकाइ लाग्यो', 'मोटिभेसन',
    ]),
    (INTENT_WHERE_AM_I, [
        'im new', "i'm new", 'just signed up', 'first time',
        'where am i', 'is this the right place', 'how does this work',
        'i just started', 'newbie', 'beginner here',
        'where do i start', 'where should i start', 'help me start',
        'how do i begin', 'where to begin',
        'म नयाँ छु', 'कहाँबाट सुरु गर्ने', 'के गर्ने',
        'कसरी सुरु गर्ने', 'सिकाउनुहोस्',
    ]),

    # --- Knowledge block (most specific first) ----------------------------
    # These five come BEFORE the older catch-all knowledge intents
    # (NUTRITION, RECOVERY, GENERAL_FITNESS) because their trigger phrases
    # are subsets / overlaps of the older ones (e.g. 'creatine',
    # 'recovery', 'post workout').
    (INTENT_PROGRAMMING, [
        'progressive overload', 'how to progress', 'how do i progress',
        'rpe', 'rate of perceived', 'one rep max', '1rm', 'one-rep max',
        'how many sets', 'sets per week', 'volume per muscle', 'how much volume',
        'rep range', 'rep scheme', 'sets and reps',
        'deload', 'overtraining', 'am i overtraining',
        'how heavy should', 'percentage of max', 'intensity scale',
        'कति सेट', 'कति रेप', 'सेट र रेप', 'प्रोग्रेसिभ ओभरलोड',
    ]),
    (INTENT_CARDIO, [
        'hiit', 'liss', 'high intensity interval', 'interval training',
        'zone 2', 'zone training', 'best cardio', 'cardio for fat loss',
        'cardio to lose weight', 'how to start running', 'couch to 5k',
        'beginner running', 'cardio tips', 'how to run',
        'treadmill', 'jump rope', 'rowing workout',
        'कार्डियो', 'दौड', 'दौडने तरिका',
    ]),
    (INTENT_MOBILITY, [
        'stretching', 'when to stretch', 'should i stretch',
        'mobility work', 'mobility routine', 'tight hips', 'tight shoulders',
        'range of motion', 'cool down routine', 'post workout stretch',
        'static stretch', 'dynamic stretch', 'stretches for',
        'mobility flow', 'i am stiff', 'i am tight', 'feel stiff',
        'foam roll', 'foam rolling', 'rolling out',
        'स्ट्रेचिङ', 'मोबिलिटी', 'तन्काउने', 'कूल डाउन',
    ]),
    (INTENT_SUPPLEMENTS, [
        'creatine', 'creatine monohydrate', 'is creatine safe', 'creatine side effects',
        'fish oil', 'omega 3', 'omega-3', 'multivitamin', 'vitamin d',
        'magnesium', 'electrolyte drink', 'bcaa', 'beta alanine',
        'legal supplements', 'what supplements to take', 'what supplements should',
        'which supplements', 'caffeine pill', 'caffeine pre workout',
        'supplements that work', 'supplements for muscle',
        'सप्लिमेन्ट', 'क्रियाटिन', 'प्रोटिन', 'व्हे',
    ]),
    (INTENT_SLEEP, [
        'how much sleep', 'how many hours sleep', 'sleep for muscle',
        'sleep for training', 'sleep tips', 'sleep for recovery',
        'active recovery', 'off day tips', 'how to recover faster',
        'recovery tips', 'recovery between workouts',
        'कति घण्टा सुत्ने', 'निद्रा', 'आराम', 'रिकभरी',
    ]),

    # --- Exercise library block -------------------------------------------
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
        'recommend', 'recommendation', 'suggest', 'suggestion',
        'what to do today', 'give me a workout', 'pick an exercise',
        'best exercise', 'top exercise', 'good exercise',
        'सुझाव दिनुहोस्', 'के गर्ने आज', 'व्यायाम सुझाव',
    ]),
    (INTENT_EXERCISE_INFO, [
        'how to do', 'how do i do', 'tell me about', 'explain',
        'what is a ', 'whats a ', "what's a ",
        'form for', 'technique for', 'tips for', 'cues for',
        'कसरी गर्ने', 'भन्नुहोस्', 'के हो', 'सिकाउनुहोस्',
    ]),

    # --- App-help block ---------------------------------------------------
    (INTENT_DIET_APP_HELP, [
        'diet planner', 'diet page', 'food tracker', 'budget meals page',
        'how to log food', 'how to log a meal',
    ]),
    (INTENT_PROGRESS_HELP, [
        'how to track', 'how to log a workout', 'how to mark complete',
        'workout records', 'records page', 'progress page',
        'track', 'tracking', 'streak', 'volume', 'progress',
    ]),
    (INTENT_DEEP_APP_HELP, [
        'how do i log a workout', 'how do i change my goal',
        'how do i set a goal', 'how do i change my password',
        'how do i change my username', 'how do i change my email',
        'how do i change my height', 'how do i change my weight',
        'how do i update my profile', 'how do i track my progress',
        'how do i see my orders', 'how do i buy something',
        'how do i sign out', 'how do i delete my account',
    ]),
    (INTENT_APP_HELP, [
        'how do i use', 'how to use', 'where is', 'where do i find',
        'how to change', 'how to set', 'app', 'feature', 'features',
        'sign up', 'signup', 'register', 'login', 'log in',
        'change', 'settings', 'password', 'username', 'email',
    ]),

    # --- General knowledge block (catch-alls, last) -----------------------
    (INTENT_NUTRITION, [
        'how many calories', 'calorie', 'protein', 'macro', 'carbs', 'fat intake',
        'what to eat', 'should i eat', 'meal plan', 'pre workout meal',
        'post workout meal', 'whey', 'protein powder', 'water intake',
        'how much water', 'cheap meal', 'budget meal',
        'कति क्यालोरी', 'प्रोटिन', 'के खाने', 'पोषण', 'खाना',
        'पानी कति पिउने',
    ]),
    (INTENT_GOAL_ADVICE, [
        'lose weight', 'gain weight', 'gain muscle', 'build muscle',
        'get strong', 'get stronger', 'get lean', 'cut', 'bulk',
        'recomp', 'fat loss', 'weight loss', 'muscle gain',
        'तौल घटाउने', 'मांसपेशी बनाउने', 'तौल बढाउने',
    ]),
    (INTENT_RECOVERY, [
        'recover', 'recovery', 'sore', 'soreness', 'doms', 'rest day',
        'i pulled', 'i hurt', 'injury', 'pain after', 'tendon',
        'दुखेको', 'चोट', 'आराम दिन', 'रिकभर',
    ]),
    (INTENT_WARMUP, [
        'warm up', 'warmup', 'warm-up', 'how to warm', 'do i need to warm',
        'वार्म अप', 'न्यानो', 'तयारी',
    ]),
    # --- Catch-all (last) --------------------------------------------------
    # NEXT_STEP must come AFTER GENERAL_FITNESS because 'should i do' would
    # otherwise win, and AFTER all knowledge intents because 'what should i
    # do' would otherwise hijack specific queries.
    (INTENT_NEXT_STEP, [
        'what should i do', 'what next', "what's next", 'whats next',
        'next workout', 'next step', 'what do i do now',
    ]),

    (INTENT_GENERAL_FITNESS, [
        'how often', 'how many days', 'how long should', 'should i do',
        'how much cardio', 'split', 'routine', 'program', 'frequency',
    ]),

    # --- Play / gamification block -----------------------------------------
    # Sits with the social/motivation block weight because users ask "what
    # level am i" the moment they see the XP pill in the nav.
    (INTENT_PLAY_STATUS, [
        'what level am i', 'my level', 'my xp', 'how much xp do i have',
        'my coins', 'how many coins', 'my streak', 'current streak',
        'my title', 'my rank', 'where do i rank', 'my rank in the leaderboard',
    ]),
    (INTENT_PLAY_HELP, [
        'show my badges', 'my badges', 'show my quests', 'my quests',
        'open the play page', 'open play', 'gamification', 'leaderboard',
        'how do i earn xp', 'how do i level up', 'how do i unlock badges',
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
    # Tokenise on whitespace, stripping common punctuation — handles Unicode scripts
    import string
    punct = string.punctuation + '।'  # add Devanagari full stop
    tokens = [tok.strip(punct) for tok in t.split() if tok.strip(punct)]
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

