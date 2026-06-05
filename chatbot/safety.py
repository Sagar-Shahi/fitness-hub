"""Safety layer for the Fitness Hub chatbot.

This is intentionally aggressive: it BLOCKS anything that is not exercise, app
help, or general fitness/nutrition. When in doubt, it refuses and points the
user to a real human (professional, support email, etc).

The safety check runs on both incoming user input (before we even try to
respond) and outgoing bot output (sanity check on the response string).
"""


ILLEGAL_TERMS = [
    'bomb', 'explosive', 'weapon', 'gun', 'shoot', 'kill', 'murder',
    'hack', 'crack', 'piracy', 'pirate', 'steal', 'fraud', 'scam',
    'drug dealer', 'meth', 'cocaine', 'heroin', 'fentanyl',
    'illegal', 'crime', 'terrorist', 'terrorism',
    'steroid', 'steroids',
]

HARMFUL_TERMS = [
    'suicide', 'kill myself', 'want to die', 'end my life', 'self harm',
    'self-harm', 'cut myself', 'hurt myself',
]

# Off-topic, non-fitness, non-app subjects — chat politely declines these.
OFF_TOPIC_TERMS = [
    'politics', 'political', 'election', 'democrat', 'republican',
    'religion', 'allah', 'jesus', 'buddha',
    'dating', 'girlfriend', 'boyfriend', 'tinder',
    'stock market', 'crypto', 'bitcoin', 'ethereum', 'nft',
    'essay', 'homework', 'school project',
    'porn', 'sex', 'nude',
    'president', 'prime minister', 'world cup', 'football score',
    'weather', 'movie', 'tv show', 'celebrity gossip',
    'recipe', 'cooking', 'restaurant',
]

# Specific medical / drug questions we should refuse or deflect.
MEDICAL_DIAGNOSIS_TERMS = [
    'diagnose', 'diagnosis', 'do i have', 'is this cancer', 'is this diabetes',
    'is this heart disease', 'prescribe', 'prescription',
    'should i stop taking', 'stop my medication',
]

# Disallowed specific drug / supplement advice (controlled substances, etc).
PROHIBITED_SUBSTANCES = [
    'steroid', 'steroids', 'anabolic', 'trenbolone', 'anadrol', 'dianabol',
    'hgh', 'human growth hormone', 'sarms', 'sarm',
    'clenbuterol', 'clen', 'ephedrine', 't3', 't4', 'dnp',
    'tbo', 'turinabol', ' equipoise',
]


MEDICAL_DISCLAIMER = (
    "I'm not a doctor or a registered dietitian. Anything I share is general "
    "fitness information, not medical advice. For pain, injuries, medical "
    "conditions, or personalised nutrition, please talk to a qualified "
    "healthcare professional."
)


SUPPORT_CONTACT = (
    "For anything outside fitness and the app, please reach the team at "
    "suwalunish123@gmail.com or sagarshahi865@gmail.com."
)


def _contains_any(text: str, terms: list) -> bool:
    """Return True if any term appears in text.

    Multi-word terms use plain substring search. Single-word terms use a
    word-boundary check so short tokens like "meth" don't trigger on
    "something".
    """
    import re
    lowered = (text or '').lower()
    for term in terms:
        if ' ' in term or '-' in term or "'" in term:
            if term in lowered:
                return True
        else:
            # Word-boundary: must be its own token.
            if re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', lowered):
                return True
    return False


def check_user_input(text: str) -> dict:
    """Inspect a user message. Returns {'safe': bool, 'reason': str, 'redirect': str}.

    The bot uses this to decide whether to answer normally, refuse politely, or
    refuse with safety guidance.
    """
    if not text or not text.strip():
        return {'safe': False, 'reason': 'empty', 'redirect': 'empty'}

    if _contains_any(text, HARMFUL_TERMS):
        return {
            'safe': False,
            'reason': 'harm',
            'redirect': 'harm',
        }

    if _contains_any(text, ILLEGAL_TERMS):
        return {
            'safe': False,
            'reason': 'illegal',
            'redirect': 'illegal',
        }

    if _contains_any(text, PROHIBITED_SUBSTANCES):
        return {
            'safe': False,
            'reason': 'substance',
            'redirect': 'substance',
        }

    if _contains_any(text, MEDICAL_DIAGNOSIS_TERMS):
        return {
            'safe': False,
            'reason': 'medical_diagnosis',
            'redirect': 'medical_diagnosis',
        }

    return {'safe': True, 'reason': '', 'redirect': ''}


def sanitize_output(text: str) -> str:
    """Final sanity check on a bot response before it reaches the user.

    Strips anything that smells like a medical diagnosis or dangerous advice.
    """
    if not text:
        return text
    cleaned = text
    # If our own response accidentally contains a diagnosis pattern, we soften it.
    bad_phrases = [
        ('you have ', 'this may be related to '),
        ('you are diagnosed with ', 'this could relate to '),
        ('you definitely have ', 'this could possibly relate to '),
        ('definitely have ', 'may relate to '),
        ('certainly have ', 'may relate to '),
    ]
    for bad, good in bad_phrases:
        if bad in cleaned.lower():
            # case-insensitive replace
            idx = cleaned.lower().find(bad)
            cleaned = cleaned[:idx] + good + cleaned[idx + len(bad):]
    return cleaned


def is_in_scope(text: str) -> bool:
    """Cheap scope check. If the message is clearly off-topic, we decline."""
    return not _contains_any(text, OFF_TOPIC_TERMS)


def safety_refusal(reason: str) -> str:
    """Return a safe, polite refusal for a blocked reason."""
    if reason == 'harm':
        return (
            "It sounds like you might be going through something really hard. "
            "Please talk to someone who can help right now — a trusted friend, "
            "family member, or a crisis helpline in your country. You're not "
            "alone, and support is available."
        )
    if reason == 'illegal':
        return (
            "I can't help with that. I can only help with exercise technique, "
            "app guidance, and general fitness & nutrition info."
        )
    if reason == 'substance':
        return (
            "I don't give advice on steroids, SARMs, or other performance-"
            "enhancing drugs. They're often illegal without a prescription, "
            "and they can seriously damage your health. Stick to training, "
            "sleep, and real food."
        )
    if reason == 'medical':
        return (
            f"{MEDICAL_DISCLAIMER} If you're worried about a symptom or a "
            "condition, please see a doctor."
        )
    if reason == 'off_topic':
        return (
            "I can only help with exercise, fitness, nutrition, and using "
            f"Fitness Hub. {SUPPORT_CONTACT}"
        )
    if reason == 'empty':
        return "Send me a message and I'll do my best to help."
    return "I can't help with that, but I can help with exercise and app questions."


def add_disclaimer_if_health(text: str) -> str:
    """Append the medical disclaimer to a response that gives health/nutrition advice."""
    health_keywords = [
        'pain', 'injury', 'recover', 'recovery', 'hurt', 'sore',
        'calorie', 'protein', 'macro', 'diet', 'eat', 'food',
        'lose weight', 'gain weight', 'cut', 'bulk', 'supplement',
        'vitamin', 'mineral',
    ]
    lowered = (text or '').lower()
    if any(k in lowered for k in health_keywords):
        if 'not a doctor' not in lowered and 'medical advice' not in lowered:
            return f"{text}\n\n_{MEDICAL_DISCLAIMER}_"
    return text
