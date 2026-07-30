"""
scripts/fake_webhook.py
Simulate Meta calling POST /webhook, so you can test the whole bot while the
app is still in Development mode (Meta refuses to deliver real webhooks then —
see PROGRESS.md Part 3). The OUTBOUND send is not blocked, so the reply really
does arrive in Messenger.

Usage (server must be running on :8000):
    python scripts/fake_webhook.py "What time do you open?"
    python scripts/fake_webhook.py --psid 37429592776655622 "សួស្តី"
"""
import argparse
import json
import sys

import httpx

# Your own PSID on this page, captured during the Part 3 diagnosis.
DEFAULT_PSID = "37429592776655622"
PAGE_ID = "110644858042565"
WEBHOOK_URL = "http://127.0.0.1:8000/webhook"

# Windows consoles default to cp1252 and choke on Khmer — force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="+", help="the customer message to simulate")
    parser.add_argument("--psid", default=DEFAULT_PSID,
                        help="sender PSID (must have messaged the page within 24h)")
    parser.add_argument("--url", default=WEBHOOK_URL)
    args = parser.parse_args()

    # Exactly the shape Meta POSTs — the same nesting webhook.py walks.
    payload = {
        "object": "page",
        "entry": [{
            "id": PAGE_ID,
            "time": 0,
            "messaging": [{
                "sender": {"id": args.psid},
                "recipient": {"id": PAGE_ID},
                "timestamp": 0,
                "message": {"mid": "fake.mid.local", "text": " ".join(args.text)},
            }],
        }],
    }

    print("POST", args.url)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        # The handler awaits the LLM before returning, so allow a generous timeout.
        response = httpx.post(args.url, json=payload, timeout=120)
    except httpx.ConnectError:
        print(f"\nCould not reach {args.url} — is the server running?")
        print("  uvicorn app.main:app --reload --port 8000")
        raise SystemExit(1)

    print("->", response.status_code, response.text)
    print("\nWatch the uvicorn console for the agent's reply, and check Messenger.")
    print("If the send fails with error code 10 (outside allowed window), message")
    print("the page again from that account and re-run.")


if __name__ == "__main__":
    main()
