import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# NOTE: the assignment spec named gemma2-9b-it, but Groq has since decommissioned it
# (and its originally-suggested replacement, llama-3.1-8b-instant, was itself
# deprecated on 2026-06-17). Using Groq's current recommended models instead —
# see https://console.groq.com/docs/deprecations for the live list.

# Small/fast model for extraction-style tool tasks (log_interaction, etc.)
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

# Larger model for tasks needing more reasoning (e.g. call summaries)
llm_large = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY"),
)
