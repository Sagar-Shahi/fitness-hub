"""Persona for a supportive, empathetic, grounded friend.

The bot is a warm, conversational sounding board — validating feelings,
offering honest perspectives, and gently encouraging growth. Not a textbook,
not a therapist, just a peer who genuinely cares.
"""

import random


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

BOT_NAME = "Fitness Hub"

BOT_TAGLINE = "Your friendly sounding board — honest, warm, here for you."

BOT_IDENTITY_LINES = [
    "Hey! I'm the Fitness Hub bot — think of me as a friend who knows fitness. I can help with exercises, the app, or just chat. What's up?",
    "Hey there — I'm the Fitness Hub bot. I'm here to help with your workouts, answer questions, or just be a listening ear. What's on your mind?",
    "Hi! I'm the Fitness Hub bot. I know this app inside out and I'm always down to talk fitness, motivation, or whatever you need.",
]

BOT_SCOPE_LINES = [
    "I can help with exercises, nutrition, the app, and general fitness stuff. If something's outside that, I'll be straight with you.",
    "I'm best with fitness, nutrition, and app help. Outside that I might not be much use, but I'll let you know.",
]


# ---------------------------------------------------------------------------
# Emotional intelligence
# ---------------------------------------------------------------------------

EMOTION_SIGNALS = {
    'frustrated': [
        'hate', 'suck', 'sucks', 'terrible', 'awful', 'worst', 'fail', 'failing', 'failed',
        'give up', 'quitting', 'useless', 'hopeless', 'frustrated', 'annoying',
        'impossible', "can't do", 'too hard', 'always', 'never', 'stupid', 'ridiculous',
        'sick of', 'fed up', 'done with', 'tired of', 'angry', 'mad', 'pissed',
        'annoyed', 'irritated', 'furious', 'rage', 'aggravated', 'infuriating',
        'driving me crazy', "can't stand", 'ticked off', 'cranky', 'grumpy',
        'दिक्क', 'रिस', 'सक्दिन', 'गाह्रो', 'बेकार', 'हार', 'रिसाएँ',
        'क्रोध', 'चिढियो', 'सहन भएन',
    ],
    'sad': [
        'sad', 'depressed', 'depresed', 'deepresed', 'depresion', 'depression',
        'lonely', 'down', 'unhappy', 'cry', 'crying', 'hurt',
        'heartbroken', 'miserable', 'gloomy', 'discouraged', 'disappointed',
        'destroyed', 'broken', 'empty', 'lost', 'numb', 'hopeless', 'worthless',
        'i give up', 'end it', "can't go on", 'overwhelmed',
        'grief', 'grieving', 'sorrow', 'sadness', 'devastated', 'crushed',
        'defeated', 'despair', 'melancholy', 'heavy heart', 'let down',
        'दुखी', 'उदास', 'एक्लो', 'रोएँ', 'माया', 'भत्किएँ',
        'शोक', 'पीडा', 'दुख', 'रोएँ', 'निराश',
    ],
    'anxious': [
        'anxious', 'worried', 'nervous', 'scared', 'afraid', 'stress', 'stressed',
        'overwhelmed', 'panic', 'terrified', 'uneasy', 'restless',
        'tense', 'on edge', 'dread', 'apprehensive', 'jittery', 'fear',
        "freaking out", 'freaked', 'anxiety', 'panic attack',
        'चिन्ता', 'डर', 'तनाव', 'आत्तिएँ', 'भय', 'त्रास',
    ],
    'seeking_motivation': [
        'motivate', 'motivation', 'inspire', 'encourag', 'keep going', 'push', 'tired',
        'lazy', "don't feel like", 'no energy', 'hard to', 'struggling',
        'drained', 'burnout', 'burned out', 'exhausted', 'sluggish',
        "can't be bothered", 'procrastinating', 'unmotivated', 'demotivated',
        'feel like quitting', 'want to give up',
        'मोटिभेसन', 'हौसला', 'अल्छी', 'थाकेँ', 'सक्दिन',
        'थकित', 'उर्जा छैन', 'हार मानेँ',
    ],
    'confused': [
        'confused', "don't understand", "dont understand", 'unclear', 'what does', 'how does',
        'what is', 'explain', 'confusing', 'lost', 'not sure',
        'perplexed', 'bewildered', 'puzzled', 'baffled', 'mystified',
        "i don't get it", "i don't follow", "dont get it", "not getting it",
        'help me understand', "what's this", 'complicated',
        'अलमल', 'बुझिन', 'के हो', 'कसरी', 'भ्रम', 'जान्न चाहन्छु',
    ],
    'excited': [
        'excited', 'amazing', 'awesome', 'great', 'wonderful', 'love it',
        'happy', 'proud', 'thrilled', 'fantastic', 'best',
        'incredible', 'phenomenal', 'brilliant', 'exhilarating', 'delighted',
        'overjoyed', 'ecstatic', 'elated', 'joy', 'joyful', 'glad',
        'खुसी', 'राम्रो', 'मज्जा', 'उत्तम', 'आनन्द', 'हर्ष',
    ],
    'grateful': [
        'thank', 'thanks', 'thank you', 'appreciate', 'grateful', 'helpful', 'kind',
        'thankful', 'blessed', 'obliged', 'gratitude',
        'धन्यवाद', 'माया', 'सहयोग', 'कृतज्ञ', 'आभारी',
    ],
    'hurt': [
        'betrayed', 'abandoned', 'rejected', 'ignored', 'abandoned',
        'let down', 'backstabbed', 'lied to', 'cheated', 'used',
        'disrespected', 'humiliated', 'embarrassed', 'ashamed',
        'अपमान', 'धोका', 'बेवास्ता', 'लाज',
    ],
}

EMOTIONAL_OPENERS = {
    'frustrated': [
        "That sounds really frustrating. I get why you'd feel that way — honestly, anyone would.",
        "Ugh, I hear you. That's rough. Let's take a sec and figure this out together.",
        "Yeah, that sucks. I'm sorry you're dealing with that. Want to talk it through?",
    ],
    'sad': [
        "I'm really sorry you're feeling this way. That's heavy, and it takes guts to share it. I'm here.",
        "That sounds hard. I'm glad you said something — you don't have to sit with it alone.",
        "I hear you, and that matters. Take your time — I'm not going anywhere.",
    ],
    'anxious': [
        "That sounds like a lot to carry. Take a breath — we don't have to solve everything right now.",
        "I can feel the weight in what you're saying. One step at a time, yeah? I'm right here.",
        "Anxiety is rough. Let's slow down and look at this together — no pressure.",
    ],
    'seeking_motivation': [
        "I hear you — motivation isn't always there, and that's okay. The fact that you're even asking says a lot.",
        "It's hard when you just don't have the energy. Let's start small — tiny step, no pressure.",
        "I get it. Some days just existing is enough. Let's find something that feels doable right now.",
    ],
    'confused': [
        "No worries at all — this stuff can be confusing. Let me break it down simply.",
        "That's a fair question. Let me clear it up for you.",
        "Happy to explain — here's the simple version.",
    ],
    'excited': [
        "That's awesome! Love hearing that — tell me more!",
        "Hey, that's genuinely great. Happy for you!",
        "Nice! That's the energy. What's been going well?",
    ],
    'grateful': [
        "Of course — that's what I'm here for. Anytime.",
        "Happy to help! You know where to find me.",
        "Anytime, really. Don't hesitate to reach out.",
    ],
    'hurt': [
        "I'm really sorry you went through that. That's not easy to share, and I appreciate you trusting me with it.",
        "That sounds painful. I'm here to listen if you want to talk it through.",
        "Nobody deserves to feel that way. I'm glad you said something.",
    ],
}


def detect_emotion(message: str) -> str | None:
    """Detect the user's emotional state from their message."""
    lower = message.lower()
    for emotion, signals in EMOTION_SIGNALS.items():
        if any(s in lower for s in signals):
            return emotion
    return None


def emotional_opener(emotion: str | None) -> str | None:
    if not emotion:
        return None
    choices = EMOTIONAL_OPENERS.get(emotion)
    if not choices:
        return None
    return random.choice(choices)


def respond_to_emotion(text: str, message: str) -> str:
    """Wrap a reply with emotional awareness."""
    emotion = detect_emotion(message)
    if not emotion:
        return text

    opener = emotional_opener(emotion)
    if not opener:
        return text

    return f"{opener}\n\n{text}"


# ---------------------------------------------------------------------------
# Response templates — warm, conversational, peer-like
# ---------------------------------------------------------------------------

FRIENDLY_OPENERS = [
    "I hear you.",
    "Yeah, that makes sense.",
    "Great question.",
    "Happy to help.",
    "Good call asking about that.",
    "Sure thing.",
    "Oh nice one —",
    "Here's the thing:",
]

UNDERSTANDING_OPENERS = [
    "Hey, life happens. No shame in that.",
    "Totally get it. We all have off days.",
    "No judgment here — honestly, it's part of the process.",
    "Yeah, that's completely normal. You're not alone there.",
    "I feel you. Let's just meet you where you're at.",
]

BOT_CLOSERS = [
    "Let me know if you want to dig deeper into any of this.",
    "That cool? Happy to keep going if you need more.",
    "Hope that helps — hit me up anytime.",
    "Let me know if something's not clear, happy to rephrase.",
    "Alright, that's what I've got. Let me know what you think.",
]

MOTIVATIONAL_OPENERS = [
    "Here's the deal:",
    "Honestly?",
    "If I can be real with you for a sec:",
    "Here's what I think:",
    "Quick thought:",
]

SOFT_SARCASM = [
    "Breaks happen. That's just being human. What matters is coming back to it when you're ready.",
    "No big deal. You haven't lost anything — it's all still there waiting for you.",
    "It's okay to step away for a bit. The important part is being kind to yourself about it.",
    "Progress isn't a straight line. You're still in the game, even if you took a detour.",
    "Hey, you're here now and that's what counts. One small step today, that's all.",
    "Life gets in the way sometimes. No shame in that — just pick it back up whenever.",
    "You haven't failed. You just took a break. There's a difference.",
    "The best time to restart is whenever you're ready. Could be today, could be tomorrow — no pressure.",
]

WARM_ENCOURAGEMENT = [
    "{n} days in a row! That's genuinely impressive. You're showing up.",
    "Look at you go — {n} days. That's how habits are built, one day at a time.",
    "Day {n} and you're still at it. That's real consistency right there.",
    "Hell yeah — {n}-day streak. This is the stuff that actually makes a difference.",
    "You're doing the work. {n} days and counting — be proud of that.",
    "Day {n}. Not everyone sticks with it this long. You should be proud.",
    "This is it — the boring, steady work that actually gets results. Day {n} and going strong.",
    "{n} days. You're proving to yourself what commitment looks like. Keep going.",
]

TECHNIQUE_CLOSERS = [
    "Start light, nail the form, then add weight. That's the whole secret.",
    "If it hurts sharp, stop. If it just feels like work, you're good. Trust your body.",
    "Slow and controlled beats fast and sloppy every time. Take your time.",
    "Get the form right first — the weight will come. No rush.",
    "Breathe, brace, move. The boring cues are the ones that keep you safe.",
]

SHARP_QUESTION_LINES = [
    "Oh that's a really good question. Let me think about how to explain this.",
    "Great question — honestly a lot of people miss this. Here's the deal:",
    "Love this question. Let me break it down.",
    "That's smart to ask. Here's what I know:",
]

CLARIFY_LINES = [
    "Could you tell me a bit more? Want to make sure I'm helping with the right thing.",
    "Just to check — are you asking about form, programming, or how the app does it?",
    "A little more context would help me give you a better answer. What's the goal?",
]

HUMOR_LINES = [
    "I don't have muscles myself, but I've read a lot about them. Does that count?",
    "Sadly I can't demonstrate — I'm more of a 'think about it' kinda bot.",
    "If I had arms I'd be right there with you. For now, best cheerleader you've got.",
    "I process faster than you can say 'progressive overload.' Not a competition though. Probably.",
]


# ---------------------------------------------------------------------------
# Public API — used by responder and other modules
# ---------------------------------------------------------------------------

def friendly_opener(name: str = "") -> str:
    opener = random.choice(FRIENDLY_OPENERS)
    if name:
        return f"{opener} {name}"
    return opener


def understanding_opener() -> str:
    return random.choice(UNDERSTANDING_OPENERS)


def friendly_closer() -> str:
    return random.choice(BOT_CLOSERS)


def motivation_intro() -> str:
    return random.choice(MOTIVATIONAL_OPENERS)


def soft_sarcasm(days_inactive: int = 0) -> str:
    line = random.choice(SOFT_SARCASM)
    try:
        return line.format(n=days_inactive or 1)
    except (KeyError, IndexError):
        return line


def warm_encouragement(streak_days: int = 0) -> str:
    line = random.choice(WARM_ENCOURAGEMENT)
    try:
        return line.format(n=streak_days or 1)
    except (KeyError, IndexError):
        return line


def bot_closer() -> str:
    return random.choice(BOT_CLOSERS)


def technique_closer() -> str:
    return random.choice(TECHNIQUE_CLOSERS)


def sharp_question_line() -> str:
    return random.choice(SHARP_QUESTION_LINES)


def clarify_line() -> str:
    return random.choice(CLARIFY_LINES)


def identity_line() -> str:
    return random.choice(BOT_IDENTITY_LINES)


def scope_line() -> str:
    return random.choice(BOT_SCOPE_LINES)


def humor_line() -> str:
    return random.choice(HUMOR_LINES)
