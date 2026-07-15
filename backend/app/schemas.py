from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    session_id: str
    message: str


class FormState(BaseModel):
    id: Optional[int] = None
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: List[str] = []
    topics_discussed: Optional[str] = None
    materials_shared: List[str] = []
    samples_distributed: List[Dict[str, Any]] = []
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: List[str] = []

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    reply: str
    tool_calls: List[Dict[str, Any]] = []
    form_state: Optional[FormState] = None
