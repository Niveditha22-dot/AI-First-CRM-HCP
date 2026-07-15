# AI-First HCP CRM — Log Interaction Screen

A pharma field rep never types directly into this form. Instead, they describe
what happened (or what needs correcting) to the **AI Assistant** on the right,
and a **LangGraph agent** — backed by Groq — extracts the structured fields and
populates the **Log Interaction form** on the left in real time.

This matches the assignment's instructional video precisely: split-screen
layout, AI-controlled form, natural-language logging and editing.

## How it works

```
Rep types in chat  ──▶  POST /api/chat  ──▶  LangGraph Agent (per session)
                                                  │
                                       ┌──────────┴──────────┐
                                       │   Groq LLM (openai/gpt-oss-20b)  │
                                       └──────────┬──────────┘
                                                  │
                          5 tools: log_interaction, edit_interaction,
                          suggest_followups, check_sample_compliance,
                          generate_call_summary
                                                  │
                                                  ▼
                                     Postgres (SQLAlchemy) + session memory
                                                  │
                                                  ▼
                          Full form_state returned ──▶ Redux ──▶ Form Panel
                                                                (re-renders live)
```

A `session_id` (generated once per browser tab) lets the backend know which
draft interaction a correction like *"actually the name was Dr. John"* applies
to, without the rep or the LLM ever needing to reference an ID.

## The 5 LangGraph tools

| Tool | Purpose |
|---|---|
| `log_interaction` **(required)** | Extracts HCP name, sentiment, topics, samples, materials shared, etc. from free text and creates a new draft — this is what first populates the form. |
| `edit_interaction` **(required)** | Given a correction, updates ONLY the mentioned fields on the session's current draft, leaving everything else untouched. |
| `suggest_followups` | Generates the "AI Suggested Follow-ups" list shown under the form, based on what was discussed. |
| `check_sample_compliance` | Checks a proposed sample handout against a 30-day quantity limit per product per HCP. |
| `generate_call_summary` | Synthesizes an HCP's past interactions into a short pre-call briefing, using the larger Groq model. |

## Tech stack

- **Frontend:** React + Redux Toolkit, Google Inter font, split-panel layout
- **Backend:** FastAPI
- **Agent framework:** LangGraph (agent rebuilt per-request, tools bound to session via closure)
- **LLM:** Groq — `openai/gpt-oss-20b` for extraction/tool tasks, `openai/gpt-oss-120b` for call-summary synthesis
- **Database:** PostgreSQL (SQLAlchemy ORM)

### A note on the LLM models used

The assignment names `gemma2-9b-it` (with `llama-3.3-70b-versatile` as a fallback).
By the time this was built, Groq had **decommissioned `gemma2-9b-it`**, and its
own suggested replacement (`llama-3.1-8b-instant`) had *also* been deprecated
as of June 17, 2026 — along with `llama-3.3-70b-versatile`. This project uses
Groq's current recommended models instead: `openai/gpt-oss-20b` (small/fast)
and `openai/gpt-oss-120b` (larger, for reasoning-heavy tasks). See
https://console.groq.com/docs/deprecations for the live list.

## Running it locally

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY and DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup. No manual HCP row is needed —
the form starts empty and is populated entirely by the AI Assistant.

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Opens on `http://localhost:3000`.

## Demoing the 5 tools

In the AI Assistant chat, try:

1. **`log_interaction`**: *"Today I met with Dr. Smith and discussed product X
   efficacy. The sentiment was positive and I shared the brochures."*
   → watch the left form populate live.
2. **`edit_interaction`**: *"Actually the name was Dr. John and the sentiment
   was negative."* → only those two fields change.
3. **`suggest_followups`**: *"What follow-ups would you suggest?"* → the AI
   Suggested Follow-ups list appears under the form.
4. **`check_sample_compliance`**: *"Can I give Dr. John 3 more units of DrugX?"*
5. **`generate_call_summary`**: *"Give me a briefing before my next call with
   Dr. John."*

## Known limitations / next steps

- Session state (which draft is "current") is stored in-memory on the backend
  and resets on restart — a production version would persist this in Redis or
  the database itself.
- `check_sample_compliance` uses a simple mock 30-day flat limit rather than
  real per-product, per-region regulatory rules.
- HCP matching for compliance/summary tools is a simple name-based `ILIKE`
  lookup rather than a proper foreign-key relationship — a deliberate
  simplification since this screen treats HCP name as a free-text AI-filled
  field, not a normalized lookup.
