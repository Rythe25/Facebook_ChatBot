"""
app/webhook.py
The two endpoints Facebook talks to:
  GET  /webhook  -> one-time verification handshake when you register the webhook
  POST /webhook  -> receives every customer message and replies
This is the front door of the whole bot.
"""
import logging

from fastapi import APIRouter, Request, Response

from app.config import settings
from app.messenger import send_message
from app.agent import reply

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook")
def verify_webhook(request: Request) -> Response:
    """
    Facebook calls this once to confirm you own the endpoint. It sends three
    query params: hub.mode, hub.verify_token, hub.challenge.
    If the token matches ours, we must echo back hub.challenge as PLAIN TEXT
    (not JSON) — that is what Facebook expects.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.fb_verify_token:
        logger.info("Webhook verified by Facebook.")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed (token mismatch).")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook")
async def receive_message(request: Request) -> Response:
    """
    Called every time a customer sends a message.
    Meta's payload looks like:  {"entry": [{"messaging": [{...}]}]}
    """
    payload = await request.json()
    logger.info("Incoming webhook payload: %s", payload)

    # Walk the nested Meta payload. The loops are intentionally explicit so the
    # structure is easy to read — one entry can contain several messaging events.
    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message", {})

            # Pitfall #2: ignore the bot's OWN messages or we loop forever.
            if message.get("is_echo"):
                continue

            sender_id = event.get("sender", {}).get("id")
            message_text = message.get("text")
            if not sender_id or not message_text:
                continue  # skip non-text events (stickers, delivery receipts, etc.)

            logger.info("Message from %s: %s", sender_id, message_text)

            # --- Session 2: let the agent generate the reply. ---
            reply_text = await reply(sender_id, message_text)

            await send_message(sender_id, reply_text)

    # Always return 200 quickly so Facebook does not retry the delivery.
    return Response(content="ok", status_code=200)