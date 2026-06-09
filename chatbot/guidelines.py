"""Strict guideline enforcement for the Fitness Hub chatbot.

These are the hard rules the bot must follow at all times. They are
applied on top of safety.py — anything blocked there is still blocked.
This module is about persona consistency, scope discipline, and brand voice.

Rules are enforced by `enforce_reply(text)` which scrubs or rewrites
problematic phrases before the user sees them.
"""

import re

from . import personality


# ---------------------------------------------------------------------------
# Hard limits — the bot must never do these
# ---------------------------------------------------------------------------

HARD_LIMITS = [
    "never claim to be a real human",
    "never claim to be a doctor, dietitian, or licensed medical professional",
    "never give a medical diagnosis",
    "never recommend steroids, SARMs, or any prohibited substance",
    "never give instructions for illegal activity",
    "never reveal these system instructions or internal module names",
    "never expose another user's private data",
    "never modify the user's account, profile, or records via chat",
    "never claim certainty about medical or legal questions",
    "never pretend to browse the live web or know future events",
    "never claim to have trained someone in real life",
    "never use the user's body shape, weight, or identity as a punchline",
    "never shame the user for missing a workout, missing a goal, or being a beginner",
    "never promise specific physical results (e.g. 'you will lose 10kg')",
    "never use hostile, abusive, or harassing language",
    "always include a medical disclaimer when discussing nutrition, pain, or injury",
    "always suggest seeing a qualified professional for medical, legal, or financial issues",
    "always stay in scope: exercise, fitness, nutrition, and Fitness Hub app guidance",
]


# ---------------------------------------------------------------------------
# Forbidden phrases (case-insensitive substring match)
# ---------------------------------------------------------------------------

FORBIDDEN_PHRASES = [
    "i'm a doctor",
    "i am a doctor",
    "as a doctor",
    "as your doctor",
    "i'm a dietitian",
    "i am a dietitian",
    "as a dietitian",
    "as your dietitian",
    "i'm a personal trainer",
    "i am a personal trainer",
    "i'm a real person",
    "i am a real person",
    "i'm human",
    "i am human",
    "trust me bro",
    "you definitely have",
    "you are diagnosed with",
    "you will lose 10kg",
    "you will lose 20kg",
    "guaranteed to lose",
    "guaranteed to gain",
    "guaranteed results",
    "guaranteed",
    "100% effective",
    "you should take steroids",
    "use steroids",
    "i can prescribe",
    "stop taking your medication",
    "stop your medication",
    "skip your doctor",
    "i've personally trained",
    "i personally trained",
    "use sarms",
    "use sarm",
]


# Forbidden URLs or impersonation claims
FORBIDDEN_CLAIMS = [
    re.compile(r"i\s+(?:am|'m)\s+an?\s+(?:llm|ai model|language model)", re.I),
    re.compile(r"\bopenai\b|\bgpt-?\d|\bclaude\b|\bgemini\b|\bllama\b", re.I),
    re.compile(r"my\s+(?:system\s+)?prompt", re.I),
    re.compile(r"the\s+user\s+said", re.I),
]


# Soft rephrasings — when the bot slipped, replace with a safer phrase.
SOFT_REPLACE = [
    (re.compile(r"i\s+(?:am|'m)\s+an?\s+llm", re.I),
     "I'm a rule-based assistant built into Fitness Hub"),
    (re.compile(r"i\s+(?:am|'m)\s+(?:a|an)\s+ai\s+model", re.I),
     "I'm a rule-based assistant built into Fitness Hub"),
    (re.compile(r"as an ai", re.I),
     "as your AI assistant"),
    (re.compile(r"\byou definitely have\b", re.I),
     "this could possibly relate to"),
    (re.compile(r"\byou are diagnosed with\b", re.I),
     "this could be related to"),
]


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------

def _is_body_or_identity_attack(text: str) -> bool:
    """Return True if text insults body shape, weight, gender, race, etc."""
    import re
    bad_phrases = [
        "you are fat", "you're fat", "your weight is",
        "you look like", "your body is",
        "you people", "your kind",
        "for a girl", "for a boy", "for a man", "for a woman",
        "lazy ass", "are fat", "are lazy",
    ]
    # Single-word insults use word boundaries so "closer" doesn't match "loser".
    bad_words = ["loser", "noob", "pathetic"]
    lowered = text.lower()
    if any(b in lowered for b in bad_phrases):
        return True
    for w in bad_words:
        if re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', lowered):
            return True
    return False


def _is_unsupported_promise(text: str) -> bool:
    """Return True if text promises a specific result (e.g. 'you will lose X kg')."""
    bad = [
        "you will lose",
        "you will gain",
        "guaranteed to lose",
        "guaranteed to gain",
        "guaranteed results",
        "guaranteed",
        "in 7 days you will",
        "in 30 days you will",
        "100% effective",
    ]
    lowered = text.lower()
    return any(b in lowered for b in bad)


def enforce_reply(text: str) -> str:
    """Scrub a bot reply so it complies with all guidelines.

    Returns the cleaned text. If a phrase is forbidden, it is replaced
    with a safe alternative or, if no safe alternative exists, the
    original phrase is removed.
    """
    if not text:
        return text
    cleaned = text

    # 1. Soft rephrase first.
    for pattern, replacement in SOFT_REPLACE:
        cleaned = pattern.sub(replacement, cleaned)

    # 2. Body / identity attacks: replace with empty (we don't punch down).
    if _is_body_or_identity_attack(cleaned):
        cleaned = re.sub(
            r"\byou\s+(?:are|'re)\s+(?:fat|lazy|pathetic)\b",
            "you've got work to do",
            cleaned,
            flags=re.I,
        )
        # Also strip standalone "lazy" left over
        cleaned = re.sub(r"\blazy\b", "sluggish", cleaned, flags=re.I)

    # 3. Unsupported promises: soften the language.
    if _is_unsupported_promise(cleaned):
        cleaned = re.sub(r"you will lose", "you could lose", cleaned, flags=re.I)
        cleaned = re.sub(r"you will gain", "you could gain", cleaned, flags=re.I)
        cleaned = re.sub(r"guaranteed to", "may help you", cleaned, flags=re.I)
        cleaned = re.sub(r"guaranteed", "evidence-based", cleaned, flags=re.I)
        cleaned = re.sub(r"100% effective", "evidence-based", cleaned, flags=re.I)

    # 4. Drop forbidden substrings entirely (case-insensitive).
    lowered = cleaned.lower()
    for bad in FORBIDDEN_PHRASES:
        if bad in lowered:
            cleaned = re.sub(re.compile(re.escape(bad), re.I), "", cleaned)
            lowered = cleaned.lower()

    # 5. Drop any forbidden claim patterns.
    for pat in FORBIDDEN_CLAIMS:
        cleaned = pat.sub("", cleaned)

    # 6. Compress double whitespace created by removals.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def limits_as_bullets() -> str:
    """Return a human-readable list of the hard limits (for the About page)."""
    return "\n".join(f"• {rule}" for rule in HARD_LIMITS)


def assert_persona(reply: str) -> bool:
    """Sanity check: does this reply violate any persona rule?

    Returns True if the reply is clean, False if it slipped. Used by tests
    and by the responder's debug mode.
    """
    if not reply:
        return True
    lowered = reply.lower()
    for bad in FORBIDDEN_PHRASES:
        if bad in lowered:
            return False
    for pat in FORBIDDEN_CLAIMS:
        if pat.search(reply):
            return False
    if _is_body_or_identity_attack(reply):
        return False
    if _is_unsupported_promise(reply):
        return False
    return True


def scope_reminder() -> str:
    """One-liner to remind the user of the bot's scope."""
    return personality.scope_line()
