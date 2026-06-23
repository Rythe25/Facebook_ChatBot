"""
app/main.py
FastAPI entrypoint. Creates the app and wires the webhook routes.
Run the dev server with:
    uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI

from app.config import settings
from app.webhook import router as webhook_router

# Configure logging so you can debug by reading the console (see PRD: Observability).
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fanpage Chatbot Capstone")

# All Facebook endpoints (GET verify + POST receive) live in app/webhook.py.
app.include_router(webhook_router)


@app.get("/")
def health_check() -> dict[str, str]:
    """Open http://localhost:8000/ in a browser to confirm the server is up."""
    return {"status": "ok"}


# TODO (Session 2): build ONE shared agent here at startup (via a FastAPI
# startup event) so we don't rebuild the agent on every incoming message.
