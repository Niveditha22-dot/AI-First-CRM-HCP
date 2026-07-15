"""
LangGraph agent that drives the Log Interaction form.

Role of the agent: it is the ONLY thing that can populate or change the form
on the left panel. The rep never types into the form directly -- they describe
what happened (or what needs correcting) in the chat panel on the right, and
this agent decides which tool to call: log a brand-new interaction, edit the
current draft, suggest follow-ups, check sample compliance, or pull a pre-call
briefing. Because the form must reflect state, the agent is rebuilt per
request with tools bound to that specific session (see build_tools_for_session),
so the LLM never needs to know or guess a session/interaction ID -- it just
calls e.g. log_interaction(raw_text=...) and the closure handles the rest.
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agent.llm import llm
from app.agent.tools import build_tools_for_session

SYSTEM_PROMPT = SystemMessage(content="""You are the AI assistant on a pharma field rep's
"Log Interaction" screen. The rep describes interactions with healthcare professionals (HCPs)
in plain English, and you populate/edit a structured form on their behalf using your tools.
You have 5 tools:

- log_interaction: use this ONLY when the rep is describing a BRAND NEW interaction that has
  not been logged yet in this conversation. If an interaction has already been logged this
  session, do NOT call log_interaction again unless the rep clearly says they're describing a
  different, separate visit/call.
- edit_interaction: use this when the rep is correcting or adding to the interaction already
  logged in this conversation (e.g. "actually it was Dr. John, not Dr. Smith").
- suggest_followups: use this whenever the rep asks for follow-up suggestions (e.g. "what
  follow-ups would you suggest?", "any next steps?"). This tool automatically reads the
  CURRENTLY logged interaction for this session -- you do NOT need the rep to re-describe it,
  and you should NOT ask them to. Just call the tool directly.
- check_sample_compliance: use this ONLY when the rep asks whether they can give/distribute
  more samples (a compliance/quantity question). Do NOT also call log_interaction for this --
  a compliance check is not the same as logging a new interaction, unless the rep separately
  and explicitly asks you to log the sample handout as part of an interaction.
- generate_call_summary: use this if the rep asks for a briefing before a call/visit.

Always call a tool rather than replying in prose when the rep describes an interaction, asks
for edits, follow-ups, a compliance check, or a briefing -- never ask the rep to repeat
information your tools can already look up from the current session. After a tool runs,
confirm back in a short, friendly sentence -- the form itself will already show the field
values, so don't re-list every field in your reply.""")


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def run_agent_for_session(session_id: str, user_message: str):
    """Builds a fresh graph bound to this session's tools and runs one turn."""
    tools = build_tools_for_session(session_id)
    llm_with_tools = llm.bind_tools(tools)

    def call_model(state: AgentState):
        messages = [SYSTEM_PROMPT] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    tool_node = ToolNode(tools)

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    graph = workflow.compile()

    from langchain_core.messages import HumanMessage
    return graph.invoke({"messages": [HumanMessage(content=user_message)]})
