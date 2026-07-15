from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from app.database import Base


class Interaction(Base):
    """
    Represents one HCP interaction "draft" as shown on the Log Interaction screen.
    This is intentionally NOT split into normalized HCP/Interaction tables --
    the assignment's screen treats every field (HCP name included) as free text
    the AI extracts and edits directly, so one flat table matches the UI 1:1.
    """
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True)  # ties a draft to one chat session

    hcp_name = Column(String(255))
    interaction_type = Column(String(50), default="Meeting")  # Meeting, Call, Email
    date = Column(String(20))   # kept as display strings -- this screen is a live
    time = Column(String(20))   # AI-filled form, not a validated date-picker
    attendees = Column(JSON, default=list)            # list[str]
    topics_discussed = Column(Text)
    materials_shared = Column(JSON, default=list)     # list[str]
    samples_distributed = Column(JSON, default=list)  # list[{"product": str, "qty": int}]
    sentiment = Column(String(20))  # "positive" | "neutral" | "negative"
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    ai_suggested_followups = Column(JSON, default=list)  # list[str]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, index=True)
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)
