"""
app/main.py
FastAPI entrypoint. Creates the app and wires the webhook routes.
Run the dev server with:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent import build_agent

from app.config import settings
from app.webhook import router as webhook_router

# Configure logging so you can debug by reading the console (see PRD: Observability).
logging.basicConfig(level=settings.log_level)
# httpx logs every outbound request URL at INFO — noisy, and it used to echo the
# page access token before messenger.py moved it into an Authorization header.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    build_agent()      # build the agent ONCE when the server starts
    yield              # app runs here; code after yield runs on shutdown

app = FastAPI(title="Fanpage Chatbot Capstone", lifespan=lifespan)

# All Facebook endpoints (GET verify + POST receive) live in app/webhook.py.
app.include_router(webhook_router)


@app.get("/")
def health_check() -> dict[str, str]:
    """Open http://localhost:8000/ in a browser to confirm the server is up."""
    return {"status": "ok"}
