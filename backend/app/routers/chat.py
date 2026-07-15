from fastapi import APIRouter
from langchain_core.messages import AIMessage, ToolMessage

from app.agent.graph import run_agent_for_session
from app.schemas import ChatMessage, AgentResponse, FormState
from app.database import SessionLocal
from app.models import Interaction
from app.session_store import get_current_interaction_id

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=AgentResponse)
def chat_with_agent(payload: ChatMessage):
    """The rep's only way of interacting with the Log Interaction form. Runs
    the LangGraph agent for this session, then returns the agent's reply plus
    the FULL current form state so the frontend can render the left panel."""
    result = run_agent_for_session(payload.session_id, payload.message)

    messages = result["messages"]
    tool_calls_trace = []
    final_reply = ""

    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_calls_trace.append({"tool": msg.name, "result": msg.content})
        if isinstance(msg, AIMessage) and msg.content:
            final_reply = msg.content

    form_state = None
    interaction_id = get_current_interaction_id(payload.session_id)
    if interaction_id:
        db = SessionLocal()
        try:
            interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if interaction:
                form_state = FormState.model_validate(interaction)
        finally:
            db.close()

    return AgentResponse(reply=final_reply, tool_calls=tool_calls_trace, form_state=form_state)
