# [AI-First-CRM-HCP](https://niveditha22-dot.github.io/AI-First-CRM-HCP/)
 
# 🩺 AI-First HCP CRM — Log Interaction Screen
 
An AI-agent-driven CRM screen for pharma field reps, built with **React + Redux**, **FastAPI**, and a **LangGraph** agent running on **Groq**.
 
The core idea: the rep never types into the form. They *describe* an interaction in plain English to an AI Assistant, and a LangGraph agent extracts the structured fields and populates a live form in real time — then edits it conversationally as the rep corrects or adds details.
> 💬 *"Today I met with Dr. Smith and discussed product X efficacy. Sentiment was positive, shared brochures."* ➡️ form fills itself out. No clicking, no typing into fields.
 
`React` `Redux Toolkit` `FastAPI` `LangGraph` `Groq` `PostgreSQL` `SQLAlchemy`
 
---
 
## 🔗 Live Demo
 
- **App:** [ai-first-crm-hcp-green.vercel.app](https://ai-first-crm-hcp-green.vercel.app) — `https://ai-first-crm-hcp-green.vercel.app`
- **API:** [ai-first-crm-hcp-rp08.onrender.com](https://ai-first-crm-hcp-rp08.onrender.com) — `https://ai-first-crm-hcp-rp08.onrender.com`
> ⏳ The backend is hosted on Render's free tier, which spins down after ~15 minutes of inactivity. If the app has been idle, the **first message may take 30–60 seconds** to respond while the server wakes up — this is expected, not a bug. Subsequent messages are fast.
 
---
 
## 🎬 Demo
 
| Rep says…                                                                                            | Tool called               | What happens                                                                              |
| ---------------------------------------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| 📝 *"Today I met with Dr. Smith, discussed product X efficacy, positive sentiment, shared brochures"* | `log_interaction`         | Form populates: HCP name, sentiment, topics, materials — all extracted from one sentence  |
| ✏️ *"Actually the name was Dr. John and sentiment was negative"*                                     | `edit_interaction`        | Only those two fields change. Everything else stays exactly as it was                     |
| 💡 *"What follow-ups would you suggest?"*                                                             | `suggest_followups`       | AI reads the current draft and proposes 2-4 concrete next steps                           |
| 🚦 *"Can I give Dr. John 3 more units of DrugX?"*                                                     | `check_sample_compliance` | Checks a 30-day distribution limit — **correctly refuses** if it's already been given out |
| 📋 *"Give me a briefing before my next call with Dr. John"*                                           | `generate_call_summary`   | Synthesizes the HCP's full interaction history into a short pre-call brief                |
 
---
 
## 🧠 Why this design is harder than it looks
 
The tricky part isn't calling an LLM — it's **state**. When a rep says *"actually it was Dr. John,"* the agent has to know *which* draft that refers to, without the rep repeating an ID and without the LLM inventing one. This project solves that with a lightweight **session-scoped draft tracker**: each browser tab gets a `session_id`, and the backend remembers which interaction row is "current" for that session — so `edit_interaction` always knows exactly what to update.
 
The 5 tools are also built **fresh per request**, as closures over that session's ID (see `build_tools_for_session()` in `tools.py`). That means the LLM never sees or needs to pass a session/interaction ID as a tool argument — it just calls `edit_interaction(correction_text=...)` and the plumbing handles the rest invisibly.
 
---
 
## 🏗️ Architecture
 
```
Rep types in chat  ──▶  POST /api/chat  ──▶  LangGraph Agent (rebuilt per session)
                                                  │
                                       ┌──────────┴──────────┐
                                       │  Groq LLM (openai/gpt-oss-20b)  │
                                       └──────────┬──────────┘
                                                  │
                    5 tools: log_interaction, edit_interaction,
                    suggest_followups, check_sample_compliance,
                    generate_call_summary
                                                  │
                                                  ▼
                         Postgres (SQLAlchemy) + in-memory session map
                                                  │
                                                  ▼
                    Full form_state returned ──▶ Redux ──▶ Form Panel
                                                          (re-renders live, read-only)
```
 
---
 
## 🛠️ The 5 LangGraph tools
 
| Tool                                | Purpose                                                                                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| ✅ `log_interaction` **(required)**  | Extracts HCP name, sentiment, topics, samples, materials shared, etc. from free text and creates a new draft for this session.             |
| ✅ `edit_interaction` **(required)** | Updates ONLY the fields mentioned in a correction, on the session's current draft — never touches unrelated fields.                        |
| 💡 `suggest_followups`               | Generates 2-4 concrete, specific next-step suggestions based on what was actually discussed.                                               |
| 🚦 `check_sample_compliance`         | Validates a proposed sample handout against a 30-day quantity limit — and will refuse a request that exceeds it.                           |
| 📋 `generate_call_summary`           | Synthesizes an HCP's full interaction history into a short pre-call briefing, using a larger model for the reasoning-heavy synthesis step. |
 
---
 
## ⚙️ Tech stack
 
- **Frontend:** React + Redux Toolkit, Google Inter font, read-only AI-driven form panel
- **Backend:** FastAPI
- **Agent framework:** LangGraph — agent rebuilt per-request with tools bound to session via closure (no global state, no ID leakage to the LLM)
- **LLM:** Groq — `openai/gpt-oss-20b` for extraction/tool-calling, `openai/gpt-oss-120b` for the reasoning-heavier call-summary task
- **Database:** PostgreSQL via SQLAlchemy
- **Deployment:** Vercel (frontend), Render (backend + managed Postgres)
### 🔧 A real problem I hit and fixed: model deprecation
 
The assignment spec names `gemma2-9b-it`. By the time this was built, Groq had **decommissioned that model outright** — and its own suggested fallback, `llama-3.1-8b-instant` (along with `llama-3.3-70b-versatile`), had *also* been deprecated as of June 17, 2026. Rather than silently failing, this project checks Groq's live model list and uses their current recommendations: `openai/gpt-oss-20b` and `openai/gpt-oss-120b`. See [Groq's deprecations page](https://console.groq.com/docs/deprecations) for the up-to-date list. This is exactly the kind of thing that breaks in production when you depend on a fast-moving inference provider — worth knowing how to detect and fix, not just work around once.
 
### 🔧 Another real problem: Python 3.14 wheel compatibility on deploy
 
Render's default Python build image picked up 3.14, which doesn't yet have prebuilt wheels for `pydantic-core` — causing the build to fail while compiling from source. Fixed by pinning the runtime explicitly via `runtime.txt` (`python-3.11.9`) and a `PYTHON_VERSION` environment variable, forcing Render to use a version with available wheels. Same root cause as the local `psycopg2` Windows wheel issue hit earlier in development — a reminder that dependency wheel availability is a real constraint to check whenever the Python version changes, not just a local dev-environment quirk.
 
---
 
## 🚀 Running it locally
 
### Backend
 
```
cd backend
python -m venv venv && source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY and DATABASE_URL
uvicorn app.main:app --reload --port 8000
```
 
Tables are created automatically on startup. No seed data needed — the form starts empty and is populated entirely by the AI.
 
### Frontend
 
```
cd frontend
npm install
npm start
```
 
Opens on `http://localhost:3000`.
 
---
 
## 🔭 Scoped out / next steps
 
- **Persistent session state** — currently in-memory, would move to Redis or the DB itself, keyed by authenticated rep ID
- **Real compliance rules** — currently a flat 30-day mock limit, would connect to actual per-product/per-region regulatory data
- **Normalized HCP records** — currently free-text name matching (`ILIKE`), would move to a proper HCP master table with foreign keys
- **Auth & roles** — would add JWT-based auth with rep vs. manager access levels
- **Cold-start latency** — move off Render's free tier (or add a keep-alive ping) so the API doesn't sleep between demo sessions
---
 
## 🎯 What this project demonstrates
 
- Designing an **agentic UI**, where the LLM's output directly drives application state rather than just producing text
- Handling **multi-turn conversational state** without leaking implementation details (session IDs, database IDs) into the LLM's tool-calling surface
- **Debugging real external-dependency failures** (model deprecation, Python wheel compatibility on deploy) and adapting rather than hard-coding around them
- Balancing 5 required tools across **must-have extraction/editing logic** and genuinely useful **sales-adjacent features** (compliance, briefings, follow-ups)
- **Deploying a full-stack AI app end-to-end** — separate frontend/backend hosts, managed Postgres, environment-based secrets, and CORS across origins
---
 
## 👩‍💻 Author
 
Built by Niveditha - feel free to reach out at nivedithar483@gmail.com for any questions.
 
