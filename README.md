<div align="center">

# 🍜 Phnom Penh Noodle House — Messenger Chatbot

**An AI customer-service bot for a Facebook Page — answers from a real menu, speaks Khmer and English, and writes confirmed orders into Google Sheets.**

[![Python](https://img.shields.io/badge/Python-3.11%20%E2%80%93%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Pinecone](https://img.shields.io/badge/Pinecone-000000?logo=pinecone&logoColor=white)](https://www.pinecone.io/)
[![Status](https://img.shields.io/badge/status-live%20on%20Messenger-success)](#)

</div>

---

## Overview

A customer messages the fanpage. The bot reads it, works out what they need, looks the answer up in a real FAQ knowledge base, and replies in the customer's own language — Khmer or English. If they want to order or reserve a table, it collects the details across the conversation and writes a row into Google Sheets once they confirm.

No hallucinated prices. No invented opening hours. Everything factual comes from `data/faqs.csv`.

> Capstone project for *Creating AI Applications Using Python* (Module 8) — **STEP IT Academy, Phnom Penh**.
> Built across four sessions: **Speak → Think → Know → Act**.

### Example

| Customer | Bot |
|---|---|
| `When is the opening time` | *"We're open 7:00 AM – 9:00 PM daily 🍜"* |
| `អ្នកមានស៊ុបប្រភេទណាខ្លះ?` | *(full Khmer reply, Khmer numerals, addresses them as បង)* |
| `2 Special Noodle delivered to St. 302 at 7pm, I'm Dara, 011 222 333` | *"Thanks Dara! …"* → row written to Google Sheets |

---

## Features

| | Capability | How it works |
|---|---|---|
| 🗣️ | **Speak** | FastAPI webhook receives every message; replies via the Facebook Graph API |
| 🧠 | **Think** | LangChain agent (Gemini or OpenAI) with per-customer conversation memory |
| 📚 | **Know** | Pinecone vector search over the FAQ — answers are grounded, never invented |
| ✅ | **Act** | Collects name, phone, order, time and order type → appends a row to Google Sheets |
| 🌏 | **Bilingual** | Detects the language from the actual script used and replies in kind |
| 🔒 | **Safe by default** | Secrets in `.env`, tokens sent as headers so they never reach the logs |

---

## How it works

```
Customer ─▶ Messenger ─▶ POST /webhook          webhook.py — filter echoes, extract text
                              │
                              ▼
                        reply()  (agent.py) ──── loads history (memory.py)
                              │
                              │  the agent decides what it needs:
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
        menu / FAQ?     confirmed order?    normal chat
      search_faq            save_booking       LLM answers
       → Pinecone           → Google Sheets    directly
              └───────────────┼────────────────┘
                              ▼
              messenger.py sends the reply ─▶ Customer
                              │
                              └─ history updated for the next turn
```

**The RAG split.** `data/faqs.csv` holds two columns and they do different jobs:

- **`answer`** — the source of truth. This is what the bot speaks from.
- **`question`** — sample phrasings. Embedded so that real customer messages (paraphrases, Khmer equivalents, typos) still match the right row.

At runtime `search_faq` embeds the incoming message, queries Pinecone (`top_k=3`, score ≥ 0.5), and hands the matching rows to the agent.

> ⚠️ Anything the bot must factually know **has to live in `faqs.csv`**, and edits only take effect after you re-run `python scripts/upload_faqs.py`.

---

## Tech stack

| Layer | Choice |
|---|---|
| Web framework | FastAPI + Uvicorn |
| LLM | Google Gemini `gemini-flash-latest` (default) — or OpenAI, switchable by env var |
| Agent framework | LangChain (`create_agent`) |
| Memory | In-process, keyed by Facebook PSID (resets on restart — by design) |
| Vector DB | Pinecone — `gemini-embedding-001`, 768 dimensions, cosine |
| Action | Google Sheets via `gspread` (service account) |
| Tunnel (dev) | ngrok |

---

## Project structure

```
app/
  main.py              FastAPI entrypoint; builds the agent once at startup (lifespan)
  config.py            all settings, loaded from .env via pydantic-settings
  webhook.py           GET /webhook (verify handshake) + POST /webhook (receive → reply)
  messenger.py         send_message() — replies through the Facebook Graph API
  agent.py             build_agent() + reply(); wires the LLM and its tools
  memory.py            per-PSID conversation history
  prompts.py           system prompt — persona, language rules, ordering rules
  tools/
    faq_search.py      @tool search_faq   — Pinecone retrieval
    sheets.py          @tool save_booking — append a row to Google Sheets
  credentials/         Google service-account JSON (git-ignored)

data/faqs.csv          the FAQ knowledge base (question,answer)
MENU.md                the full menu the FAQ data is derived from

scripts/
  create_index.py      create the Pinecone index          (run once)
  upload_faqs.py       embed faqs.csv and upsert          (run once, and after every edit)
  local_test.py        chat with the agent from a terminal (no Facebook needed)

docs/                  PRD.md, ARCHITECTURE.md, SPRINT_PLAN.md
PROGRESS.md            build log, root-cause write-ups, verification record
```

---

## Prerequisites

Before you start, get these five things:

| # | What | Where | Cost |
|---|---|---|---|
| 1 | **Python 3.11 – 3.13** | [python.org](https://www.python.org/downloads/) | free |
| 2 | **Facebook Page** you're admin of, plus an App with the **Messenger** product | [developers.facebook.com](https://developers.facebook.com/) | free |
| 3 | **Gemini API key** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | free tier |
| 4 | **Pinecone account** | [app.pinecone.io](https://app.pinecone.io/) | free Starter tier |
| 5 | **Google Cloud service account** with the Sheets + Drive APIs enabled | [console.cloud.google.com](https://console.cloud.google.com/) | free |
| 6 | **ngrok** | [ngrok.com](https://ngrok.com/) | free tier |

---

## Setup

### 1. Clone and create the virtual environment

```powershell
git clone https://github.com/Rythe25/Facebook_ChatBot.git
cd Facebook_ChatBot

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1          # your prompt should now show (.venv)
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Every new terminal needs the venv activated** (`.\.venv\Scripts\Activate.ps1`).
> On macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`.

### 2. Create your `.env`

```powershell
Copy-Item .env.example .env
```

Then open `.env` and fill in the values. Each one is explained in the file itself, and in [Configuration](#configuration) below.

> ⚠️ **`config.py` rejects unknown keys.** A misspelled variable (say `GEMINI_API_KEY` instead of `GOOGLE_API_KEY`) raises `ValidationError: Extra inputs are not permitted` at import time and **nothing** starts — not the server, not the scripts. If the app dies instantly on launch, check `.env` first.

### 3. Set up Pinecone

```powershell
python scripts/create_index.py     # creates the 768-dimension index
python scripts/upload_faqs.py      # embeds data/faqs.csv and uploads (21 rows)
```

Expect `upload_faqs.py` to report the number of vectors upserted. If retrieval later returns nothing, this is the first thing to re-run.

### 4. Set up Google Sheets

1. In Google Cloud, create a **service account** and enable the **Google Sheets API** and **Google Drive API**.
2. Create a JSON key and save it to `app/credentials/service_account.json`.
3. Create a Google Sheet. Give the first tab this header row:

   | Timestamp | Name | Phone | Order type | Order | Preferred time | Notes |
   |---|---|---|---|---|---|---|

4. **Share the sheet with the service account's `client_email` as Editor.** Skip this and `save_booking` fails with `403 caller does not have permission`.
5. Copy the sheet ID from its URL — `/spreadsheets/d/`**`THIS_PART`**`/edit` — into `GOOGLE_SHEETS_ID`.

### 5. Start the server and the tunnel

Two terminals:

```powershell
# Terminal 1
.\.venv\Scripts\Activate.ps1
chcp 65001                                    # UTF-8 console, or Khmer log lines crash the logger
uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 2
ngrok http 8000                               # copy the https://....ngrok-free.dev URL
```

Terminal 1 should print `Agent built (provider=gemini).` and `Application startup complete.`
Open <http://localhost:8000/> — you should see `{"status": "ok"}`.

### 6. Wire up Meta — **both** subscriptions

This is the step that catches everyone. Meta has **two separate subscriptions** and you need both:

| # | Where in the App Dashboard | What it means |
|---|---|---|
| **1** | **Webhooks** product page | *"My app is interested in `messages` events"* |
| **2** | **Messenger → Messenger API Settings** | *"**This Page** routes its events to my app"* |

**Step 1 — Webhooks page:**
- **Callback URL:** `https://<your-ngrok-url>/webhook`
- **Verify token:** exactly the value of `FB_VERIFY_TOKEN` in your `.env`
- Click **Verify and Save** — it should succeed immediately
- Subscribe to the **`messages`** field

**Step 2 — Messenger API Settings:**
- Connect your Page and generate a **Page Access Token** → paste into `FB_PAGE_ACCESS_TOKEN`
- **Subscribe the Page to your app** in the same section

If you only do step 1, everything *looks* configured and **zero webhooks arrive** — the tunnel log stays completely empty. See [Troubleshooting](#troubleshooting).

> **You do not need to publish the app.** Development mode delivers messages fine once step 2 is done. Publishing (App Review, Advanced Access) is only required to serve the general public.

### 7. Message your Page

Send it a message. Terminal 1 should show:

```
INFO:app.webhook:Incoming webhook payload: {...}
INFO:app.webhook:Message from 374295927766xxxxx: When is the opening time
INFO:pinecone.index:Querying index with top_k=3
INFO:app.messenger:Sent reply to 374295927766xxxxx
INFO:     "POST /webhook HTTP/1.1" 200 OK
```

> ⚠️ **ngrok's free URL changes every time you restart it.** Re-paste the new URL into step 1 each time, or delivery silently stops with no error anywhere.

---

## Configuration

All settings live in `.env` and are loaded by `app/config.py`.

| Variable | Required | Description |
|---|:---:|---|
| `FB_VERIFY_TOKEN` | ✅ | Any string you invent; must match the Meta webhook config exactly |
| `FB_PAGE_ACCESS_TOKEN` | ✅ | Page Access Token from Messenger API Settings |
| `LLM_PROVIDER` | ✅ | `gemini` (default) or `openai` |
| `GOOGLE_API_KEY` | ✅ | Gemini key — also used for embeddings, so required either way |
| `OPENAI_API_KEY` | – | Only when `LLM_PROVIDER=openai` |
| `PINECONE_API_KEY` | ✅ | Starts with `pcsk_` |
| `PINECONE_INDEX_NAME` | – | Default `fanpage-faqs` |
| `GOOGLE_SHEETS_ID` | ✅ | The id between `/d/` and `/edit` in the sheet URL |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | – | Default `app/credentials/service_account.json` |
| `LOG_LEVEL` | – | Default `INFO` |

---

## Testing

Two tiers — start with the cheap one.

**Agent only** (no Facebook, no ngrok, no Meta dashboard):

```powershell
python scripts/local_test.py "What time do you open?"    # one-shot
python scripts/local_test.py                             # interactive — tests memory
```

This exercises the LLM, the system prompt, RAG retrieval, Google Sheets, and conversation memory. Interactive mode is the easiest way to walk through a full ordering flow.

**Real Messenger** — message the Page. Covers everything, plus Meta's delivery and your tunnel.

> **24-hour messaging window:** the outbound send only succeeds if that person messaged the Page within the last 24 hours. Error code `10` / *"outside allowed window"* means it lapsed — message the Page again from that account and retry.

---

## Troubleshooting

Real failures hit during this build, with the checks that actually resolve them.

<details>
<summary><b>The bot never replies, and nothing appears in the server log</b></summary>

<br>

Work outward from your machine — each check rules out one layer:

```powershell
# 1. Is the app even running?
curl http://127.0.0.1:8000/                      # expect {"status": "ok"}

# 2. Is ngrok pointed at the right port?
curl http://127.0.0.1:4040/api/tunnels

# 3. Did Meta send anything at all?
curl http://127.0.0.1:4040/api/requests/http     # "requests":[] means Meta sent NOTHING

# 4. Does a request survive the whole path?
curl "https://<ngrok>/webhook?hub.mode=subscribe&hub.verify_token=x&hub.challenge=PING"
#    "Verification failed" is a SUCCESS here — it proves your handler was reached
```

If check 3 returns an empty list, no amount of Python debugging will help — the problem is on the Meta side. The usual cause is the **missing Page-level subscription** (setup step 6, part 2).
</details>

<details>
<summary><b>Meta sends webhooks but every one returns 502 Bad Gateway</b></summary>

<br>

ngrok is up but has nothing behind it. `ngrok http 8000` stays running happily even when uvicorn has crashed or was never started — and from the Meta dashboard it looks identical to a misconfiguration.

Check `curl http://127.0.0.1:8000/` first. If that fails, restart uvicorn and read its startup output.
</details>

<details>
<summary><b>The app exits instantly on startup</b></summary>

<br>

Reproduce the error without the server in the way:

```powershell
python -c "import app.main"
```

This triggers every import-time connection. Common causes:

| Error | Cause |
|---|---|
| `ValidationError: Extra inputs are not permitted` | An unknown key in `.env` — every name must match a field in `config.py` |
| `404 NOT_FOUND: Resource fanpage-faqs not found` | Pinecone index missing — run `scripts/create_index.py` |
| `APIError [403] caller does not have permission` | Sheet not shared with the service account's `client_email` |
| `error while attempting to bind on address` | Port 8000 already in use — another uvicorn is still running |
| `404: model ... is no longer available` | Retired Gemini model — `agent.py` uses `gemini-flash-latest` |
</details>

<details>
<summary><b>Webhook verification fails in the Meta dashboard</b></summary>

<br>

`FB_VERIFY_TOKEN` in `.env` must match the dashboard field character for character. Restart uvicorn after changing `.env` — settings are read once at import, so `--reload` does not always pick it up.
</details>

<details>
<summary><b>Khmer text crashes the console with a UnicodeEncodeError</b></summary>

<br>

Windows terminals default to cp1252. Run `chcp 65001` before starting uvicorn.
</details>

<details>
<summary><b>The bot answers with old or wrong menu facts</b></summary>

<br>

Edits to `data/faqs.csv` do nothing until the vectors are rebuilt:

```powershell
python scripts/upload_faqs.py
```
</details>

---

## Customising it for your own business

1. Rewrite `MENU.md` with your real products and prices.
2. Rewrite `data/faqs.csv` — the `answer` column is what the bot will say, the `question` column is sample phrasings for matching.
3. Re-run `python scripts/upload_faqs.py`.
4. Edit the persona, tone, and language rules in `app/prompts.py`.
5. Adjust the Sheets columns in `app/tools/sheets.py` if you need different fields.

---

## Security

- **Secrets never enter git.** `.env` and `app/credentials/` are git-ignored — verify with `git ls-files` before pushing.
- **Tokens stay out of logs.** `messenger.py` sends the Page token as an `Authorization: Bearer` header rather than a query parameter, because httpx logs full request URLs at INFO — a token in the querystring gets printed on every single reply. `httpx`'s logger is also pinned to `WARNING` in `main.py`.
- **Rotate anything exposed.** If a token ever reaches a log, a screenshot, or a paste, regenerate it — the fix stops future leaks, it doesn't retract past ones.
- The app runs in Facebook **Development mode**, which serves anyone with a role on the app or Page. Serving the general public requires publishing the app and Advanced Access for `pages_messaging`.

---

## Branches

| Branch | Contents |
|---|---|
| **`main`** | The complete project — all four capabilities |
| `session1` | Echo bot + Session 1 guide |
| `session2` | + LangChain agent & memory + Session 2 guide |
| `session3` | + Pinecone RAG + Session 3 guide |
| `session4` | + Google Sheets booking + Session 4 guide |

Each `sessionN` branch is a working checkpoint with its own step-by-step guide.

---

## Project history

[`PROGRESS.md`](PROGRESS.md) is the honest build log — including the diagnosis that was **wrong** and how it got corrected. Worth reading if you're debugging something similar.

---

<div align="center">

Capstone for **STEP IT Academy · AI Module 8** — Phnom Penh 🇰🇭

</div>
