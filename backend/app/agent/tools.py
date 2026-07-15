"""
The 5 tools available to the HCP Interaction Agent, matching the assignment's
instructional video: the AI assistant (right panel) is the ONLY thing that can
populate or change the Log Interaction form (left panel). The user never types
into the form directly.

1. log_interaction          - required. Extracts fields from free text and
                               creates a new draft interaction for this session.
2. edit_interaction         - required. Updates only the fields mentioned in a
                               correction, on the session's current draft.
3. suggest_followups        - generates the "AI Suggested Follow-ups" list.
4. check_sample_compliance  - validates a sample handout against a 30-day limit.
5. generate_call_summary    - pre-call briefing from an HCP's past interactions.

IMPORTANT: these tool functions are built fresh per-request by
build_tools_for_session() in graph.py, with session_id captured via closure.
This is what lets the LLM call e.g. log_interaction(raw_text=...) without ever
needing to know or pass a session_id itself.
"""
import json
from datetime import datetime, timedelta
from langchain_core.tools import tool

from app.database import SessionLocal
from app.models import Interaction, AuditLog
from app.session_store import get_current_interaction_id, set_current_interaction_id
from app.agent.llm import llm, llm_large

SAMPLE_LIMITS = {"default": 4}

EXTRACTION_PROMPT = """You are the AI assistant behind a life-sciences CRM's "Log Interaction"
screen. A field rep just described an interaction with a healthcare professional (HCP) in free
text. Extract the following as strict JSON:

- hcp_name (string)
- interaction_type (one of: "Meeting", "Call", "Email"; default "Meeting" if unclear)
- date (string, e.g. "Today" or an actual date if mentioned)
- time (string, e.g. "Now" or an actual time if mentioned)
- attendees (list of strings, can be empty)
- topics_discussed (string, concise)
- materials_shared (list of strings, e.g. ["Brochures"], empty list if none mentioned)
- samples_distributed (list of objects: {{"product": str, "qty": int}}, empty list if none)
- sentiment (one of: "positive", "neutral", "negative")
- outcomes (string, 1 sentence, can be empty string)

Free text:
\"\"\"{text}\"\"\"

Respond with ONLY the JSON object, no extra commentary, no markdown fences.
"""

EDIT_PROMPT = """You are the AI assistant behind a life-sciences CRM's "Log Interaction" screen.
The rep is correcting or adding to an already-logged interaction. Below is the CURRENT state of
the form, followed by the rep's correction in free text. Return ONLY a JSON object containing
JUST the fields that should change (do not include unchanged fields). Valid field names:
hcp_name, interaction_type, date, time, attendees, topics_discussed, materials_shared,
samples_distributed, sentiment, outcomes, follow_up_actions.

Current form state:
{current_state}

Rep's correction:
\"\"\"{text}\"\"\"

Respond with ONLY the JSON object of changed fields, no commentary, no markdown fences.
"""


def _parse_llm_json(content: str, fallback: dict) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json", "", 1).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return fallback


def _interaction_to_dict(interaction: Interaction) -> dict:
    return {
        "id": interaction.id,
        "hcp_name": interaction.hcp_name,
        "interaction_type": interaction.interaction_type,
        "date": interaction.date,
        "time": interaction.time,
        "attendees": interaction.attendees or [],
        "topics_discussed": interaction.topics_discussed,
        "materials_shared": interaction.materials_shared or [],
        "samples_distributed": interaction.samples_distributed or [],
        "sentiment": interaction.sentiment,
        "outcomes": interaction.outcomes,
        "follow_up_actions": interaction.follow_up_actions,
        "ai_suggested_followups": interaction.ai_suggested_followups or [],
    }


def build_tools_for_session(session_id: str):
    """Builds the 5 tools bound to one chat session via closure over session_id."""

    @tool
    def log_interaction(raw_text: str) -> str:
        """Extract structured fields (HCP name, sentiment, topics, samples, etc.)
        from the rep's free-text description of an interaction, and populate a
        brand new Log Interaction form with them. Use this the FIRST time a rep
        describes a new interaction in this conversation."""
        db = SessionLocal()
        try:
            prompt = EXTRACTION_PROMPT.format(text=raw_text)
            response = llm.invoke(prompt)
            extracted = _parse_llm_json(response.content, fallback={
                "hcp_name": None, "interaction_type": "Meeting", "date": "Today",
                "time": "Now", "attendees": [], "topics_discussed": raw_text[:200],
                "materials_shared": [], "samples_distributed": [], "sentiment": "neutral",
                "outcomes": "",
            })

            interaction = Interaction(
                session_id=session_id,
                hcp_name=extracted.get("hcp_name"),
                interaction_type=extracted.get("interaction_type", "Meeting"),
                date=extracted.get("date", "Today"),
                time=extracted.get("time", "Now"),
                attendees=extracted.get("attendees", []),
                topics_discussed=extracted.get("topics_discussed"),
                materials_shared=extracted.get("materials_shared", []),
                samples_distributed=extracted.get("samples_distributed", []),
                sentiment=extracted.get("sentiment"),
                outcomes=extracted.get("outcomes", ""),
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)

            set_current_interaction_id(session_id, interaction.id)
            return json.dumps(_interaction_to_dict(interaction))
        finally:
            db.close()

    @tool
    def edit_interaction(correction_text: str) -> str:
        """Apply a correction to the CURRENT draft interaction in this session
        (e.g. "actually the name was Dr. John and sentiment was negative").
        Updates ONLY the fields mentioned, leaving everything else unchanged."""
        db = SessionLocal()
        try:
            interaction_id = get_current_interaction_id(session_id)
            if not interaction_id:
                return json.dumps({"error": "No interaction logged yet in this session."})

            interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"error": f"interaction {interaction_id} not found"})

            current_state = json.dumps(_interaction_to_dict(interaction))
            prompt = EDIT_PROMPT.format(current_state=current_state, text=correction_text)
            response = llm.invoke(prompt)
            changes = _parse_llm_json(response.content, fallback={})

            for field, new_value in changes.items():
                if hasattr(interaction, field):
                    old_value = getattr(interaction, field)
                    old_value_str = old_value if isinstance(old_value, str) else json.dumps(old_value)
                    setattr(interaction, field, new_value)
                    db.add(AuditLog(
                        interaction_id=interaction.id,
                        field_changed=field,
                        old_value=old_value_str,
                        new_value=new_value if isinstance(new_value, str) else json.dumps(new_value),
                    ))

            interaction.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(interaction)
            return json.dumps(_interaction_to_dict(interaction))
        finally:
            db.close()

    @tool
    def suggest_followups() -> str:
        """Generate 2-4 suggested follow-up actions for the CURRENT draft
        interaction (e.g. scheduling a meeting, sending literature, adding the
        HCP to a list), based on what was discussed. Populates the 'AI
        Suggested Follow-ups' section of the form."""
        db = SessionLocal()
        try:
            interaction_id = get_current_interaction_id(session_id)
            if not interaction_id:
                return json.dumps({"error": "No interaction logged yet in this session."})

            interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"error": f"interaction {interaction_id} not found"})

            prompt = (
                f"Based on this HCP interaction, suggest 2-4 short, specific follow-up actions "
                f"a pharma field rep should take next. Return ONLY a JSON list of strings, no "
                f"commentary.\n\nHCP: {interaction.hcp_name}\nTopics: {interaction.topics_discussed}\n"
                f"Sentiment: {interaction.sentiment}\nOutcomes: {interaction.outcomes}"
            )
            response = llm.invoke(prompt)
            suggestions = _parse_llm_json(response.content, fallback=[
                "Schedule a follow-up meeting in 2 weeks",
            ])
            if not isinstance(suggestions, list):
                suggestions = [str(suggestions)]

            interaction.ai_suggested_followups = suggestions
            db.commit()
            db.refresh(interaction)
            return json.dumps({"ai_suggested_followups": suggestions})
        finally:
            db.close()

    @tool
    def check_sample_compliance(hcp_name: str, product: str, qty: int) -> str:
        """Check whether distributing a given quantity of a product sample to
        an HCP is within a 30-day compliance limit, based on past logged
        interactions for that HCP name. Returns allowed (bool) and reason."""
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=30)
            interactions = (
                db.query(Interaction)
                .filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"), Interaction.created_at >= cutoff)
                .all()
            )
            total_given = 0
            for i in interactions:
                for s in (i.samples_distributed or []):
                    if s.get("product", "").lower() == product.lower():
                        total_given += s.get("qty", 0)

            limit = SAMPLE_LIMITS.get(product, SAMPLE_LIMITS["default"])
            projected = total_given + qty
            allowed = projected <= limit

            return json.dumps({
                "allowed": allowed,
                "product": product,
                "already_given_30d": total_given,
                "requested_qty": qty,
                "limit_30d": limit,
                "reason": (
                    "Within compliance limits." if allowed
                    else f"Exceeds 30-day limit of {limit} units for {product}."
                ),
            })
        finally:
            db.close()

    @tool
    def generate_call_summary(hcp_name: str) -> str:
        """Generate a pre-call briefing for an HCP by reviewing their past
        logged interactions (matched by name). Uses the larger model to
        synthesize history into a short briefing."""
        db = SessionLocal()
        try:
            interactions = (
                db.query(Interaction)
                .filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
                .order_by(Interaction.created_at.desc())
                .limit(10)
                .all()
            )
            if not interactions:
                return json.dumps({"summary": f"No prior interactions logged for {hcp_name}."})

            history_text = "\n".join(
                f"- [{i.created_at.date()}] {i.topics_discussed} (sentiment: {i.sentiment})"
                for i in interactions
            )
            prompt = (
                f"Summarize this HCP's interaction history into a 3-4 sentence pre-call "
                f"briefing for a field rep. HCP: {hcp_name}.\n\nHistory:\n{history_text}\n\nBriefing:"
            )
            response = llm_large.invoke(prompt)
            return json.dumps({"hcp_name": hcp_name, "briefing": response.content.strip()})
        finally:
            db.close()

    return [
        log_interaction,
        edit_interaction,
        suggest_followups,
        check_sample_compliance,
        generate_call_summary,
    ]
