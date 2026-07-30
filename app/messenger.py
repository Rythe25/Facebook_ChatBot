"""
app/messenger.py
Sends replies back to the customer through the Facebook Graph API.
One job: take a recipient PSID + text and POST it to Facebook.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# v22.0 is the Graph API version this course targets.
GRAPH_API_URL = "https://graph.facebook.com/v22.0/me/messages"


async def send_message(recipient_id: str, text: str) -> None:
    """Send `text` to the customer identified by `recipient_id` (their PSID)."""
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    # Pass the token as a Bearer header, NOT a query param. httpx logs the full
    # request URL at INFO level, so a token in the querystring gets printed to
    # the console — and into any captured log file — on every single reply.
    headers = {"Authorization": f"Bearer {settings.fb_page_access_token}"}

    # NOTE on pitfall #1 (newline/quote escaping): the old n8n build broke
    # because it hand-built the JSON string. Here we pass `json=payload` and
    # httpx serializes it correctly, so special characters are handled for us —
    # do NOT manually escape, or you'll double-escape and send literal "\n".
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GRAPH_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("Sent reply to %s", recipient_id)
    except httpx.HTTPError as error:
        # Log loudly but don't crash the webhook — one failed send must not kill the bot.
        # Also include Facebook's response body (it usually says exactly what's wrong).
        body = getattr(getattr(error, "response", None), "text", None)
        logger.error("Failed to send message to %s: %s | Facebook response: %s",
                     recipient_id, error, body)
