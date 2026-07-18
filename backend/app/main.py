from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First HCP CRM", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://niveditha22-dot.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "AI-First HCP CRM backend"}
