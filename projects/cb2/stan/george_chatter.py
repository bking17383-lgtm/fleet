#!/usr/bin/env python3
"""George — varied spoken lines so she doesn't repeat one phrase."""
from __future__ import annotations

import random

EMPTY_REPLIES = (
    "Didn't land — say it again?",
    "One more time, Brian?",
    "I missed that — try again?",
    "Say that again?",
    "Hmm — didn't catch it.",
    "Run that by me again?",
)

FALLBACK_REPLIES = (
    "Yeah — what's the move?",
    "Go ahead, Brian.",
    "Talk to me.",
    "What's up?",
    "Say more.",
    "Got the mic — what do you need?",
    "Crew's here. What's next?",
    "Daddy's on back-end — I'm on the mic. Shoot.",
)

GREET_REPLIES = (
    "Hey Brian.",
    "Yeah?",
    "George on the line.",
    "Hey — what do you need?",
    "Talk to me.",
)

ACK_REPLIES = (
    "Got it.",
    "Okay.",
    "On it.",
    "Copy.",
    "Roger.",
    "Heard you.",
)


def pick(pool: tuple[str, ...]) -> str:
    return random.choice(pool)


def empty_reply() -> str:
    return pick(EMPTY_REPLIES)


def fallback_reply() -> str:
    return pick(FALLBACK_REPLIES)


def greet_reply() -> str:
    return pick(GREET_REPLIES)


def ack_reply() -> str:
    return pick(ACK_REPLIES)
