Based on the project layout I can see (FastAPI-style app under `app/`, `.env.example`, Pinecone RAG, Google Sheets), here's the typical way to run and test it. A couple of these are inferred from the structure — check `README.md` for exact commands.

## 1. Setup
```bash
# create + activate a virtualenv
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell

# install deps (whichever the repo uses)
pip install -r requirements.txt
```

## 2. Configure environment
```bash
cp .env.example .env          # then fill in the real values
```
You'll need to set (based on what the code imports via `app/config.py`):
- `LLM_PROVIDER` (`gemini` or `openai`) + `GOOGLE_API_KEY` / `OPENAI_API_KEY`
- Pinecone key/index (for `faq_search`)
- `GOOGLE_SHEETS_CREDENTIALS_PATH` + `GOOGLE_SHEETS_ID` (for `save_booking`)
- Messenger `PAGE_ACCESS_TOKEN` and `VERIFY_TOKEN` for the webhook

## 3. Ingest the FAQ (important after the refactor)
Since `data/faqs.csv` was just rewritten, the Pinecone index must be re-embedded before RAG returns the new noodle answers. Look for an ingest/embed script (often something like `python -m app.tools.faq_search` or a `scripts/ingest.py`) and run it.

## 4. Run the server
It's an ASGI app, so:
```bash
uvicorn app.main:app --reload --port 8000
```

## 5. Test it
- **Locally without Messenger** — the fastest way is to call `agent.reply()` directly:
  ```python
  import asyncio
  from app.agent import build_agent, reply
  build_agent()
  print(asyncio.run(reply("test-user", "What time do you open?")))
  print(asyncio.run(reply("test-user", "តើបងលក់មីអីខ្លះ?")))  # Khmer
  ```
  This exercises the RAG + language logic without needing Facebook.
- **Webhook** — expose the port with `ngrok http 8000`, register the URL in the Meta app dashboard, and the `GET /webhook` verify + `POST /webhook` message flow will work end-to-end.

Quick sanity checks worth running: opening hours (`7AM–9PM`), a price question (Special Noodle = 15,000 riel), and an order/reservation flow to confirm `save_booking` writes to the sheet.

I don't have the exact dependency-install or ingest command memorized — `README.md` in the repo should have the authoritative versions.