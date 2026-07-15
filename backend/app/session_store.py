"""
Very small in-memory store mapping a chat session_id to the interaction it's
currently drafting. This is what lets "actually the name was Dr. John" work
without the user (or the LLM) needing to know or pass an interaction ID --
the session remembers which draft is "current" for that browser tab.

NOTE: in-memory only, resets on backend restart. That's a fine tradeoff for
this assignment; a production version would persist this in Redis or the DB.
"""
from typing import Dict, Optional

_session_drafts: Dict[str, int] = {}


def get_current_interaction_id(session_id: str) -> Optional[int]:
    return _session_drafts.get(session_id)


def set_current_interaction_id(session_id: str, interaction_id: int) -> None:
    _session_drafts[session_id] = interaction_id
