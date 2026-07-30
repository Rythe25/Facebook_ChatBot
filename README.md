# Phnom Penh Noodle House — Fanpage Chatbot 🍜

An AI customer-service chatbot for a **Facebook Messenger** fanpage (persona: *Phnom Penh Noodle House*, a local Khmer & Chinese noodle shop in BKK1).
It chats with customers in **Khmer or English**, answers questions from a **real FAQ knowledge base**, and **writes orders and table reservations straight into Google Sheets** — no hallucinated prices or hours.

> Capstone project for *Creating AI Applications Using Python* (Module 8) — **STEP IT Academy, Phnom Penh**.
> Built in four sessions: **Speak → Think → Know → Act**.

---

## What it does

| Capability | How |
|---|---|
| 🗣️ **Speak** | Receives every message via a FastAPI webhook and replies through the Facebook Graph API |
| 🧠 **Think** | A LangChain agent (Gemini or OpenAI) with **per-customer conversation memory** |
| 📚 **Know** | Answers FAQs via **Pinecone RAG** — grounded in the real menu, never invented |
| ✅ **Act** | Collects an order or reservation (name · phone · order · time) and appends a row to **Google Sheets** |
| 🌏 **Bilingual** | Replies in the language the customer wrote in — Khmer or English, Khmer numerals included |

---

## How it works

```
Customer ─▶ Messenger ─▶ POST /webhook            (webhook.py: filter echoes, extract text)
                              │
                              ▼
                        reply()  (agent.py)  ── loads history (memory.py)
                              │  agent decides:
              ┌───────────────┼────────────────┐
              ▼               ▼                 ▼
         menu / FAQ?     "order / book"?    normal chat
      search_faq→Pinecone  save_booking→Sheet   LLM answers
              └───────────────┼────────────────┘
                              ▼
                     messenger.py sends the reply ─▶ Customer  (+ memory updated)
```

---

## Tech stack

- **Web:** FastAPI + Uvicorn
- **LLM:** Google Gemini (`gemini-flash-latest`, default) or OpenAI — switchable by env var
- **Agent:** LangChain (`create_agent`)
- **Memory:** in-memory, keyed by Facebook PSID (resets on restart — by design)
- **Knowledge (RAG):** Pinecone + Gemini embeddings (`gemini-embedding-001`, 768-dim, cosine)
- **Action:** Google Sheets via `gspread` (service account)
- **Tunnel:** ngrok (public HTTPS for local dev)

---

## Project structure

```
app/
  main.py            FastAPI entrypoint; builds the agent once at startup (lifespan)
  config.py          all settings, loaded from .env (pydantic-settings)
  webhook.py         GET /webhook (verify) + POST /webhook (receive → reply)
  messenger.py       send_message() via Facebook Graph API
  agent.py           build_agent() + reply(); wires the LLM and tools
  memory.py          per-PSID conversation history
  prompts.py         system prompt (persona + language rules)
  tools/
    faq_search.py    @tool search_faq — Pinecone retrieval
    sheets.py        @tool save_booking — append a row to Google Sheets
  credentials/       Google service-account.json (git-ignored — never committed)
data/faqs.csv        FAQ knowledge base (question,answer)
MENU.md              the full menu the FAQ data is derived from
scripts/
  create_index.py    create the Pinecone index (run once)
  upload_faqs.py     embed faqs.csv and upsert to Pinecone (run once, and after every edit)
  local_test.py      chat with the agent from the terminal (no Facebook needed)
  fake_webhook.py    POST a Meta-shaped payload to your own /webhook (no ngrok needed)
docs/                PRD.md, ARCHITECTURE.md, SPRINT_PLAN.md
PROGRESS.md          build log, root-cause notes, and the verification record
```

---

## Prerequisites

- **Python 3.11–3.13**
- A Facebook account + a **fanpage** you are admin of, and a Facebook App with the **Messenger** product
- A **Google AI Studio** API key (free — for Gemini)
- A **Pinecone** account (free Starter tier)
- A **Google Cloud** service account with **Sheets + Drive API** enabled, and a Google Sheet shared with it
- **ngrok** (free account) for local HTTPS

---

## Setup

**1. Create the virtual environment and install dependencies**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1                 # prompt should show (.venv)
python -m pip install --upgrade pip
pip install -r requirements.txt
```
> Every new terminal: **activate the venv first** (`.\.venv\Scripts\Activate.ps1`).

**2. Configure `.env`** (copy the template, then fill in the values below)
```powershell
Copy-Item .env.example .env
```
> ⚠️ `config.py` rejects unknown keys. A stray or misspelled variable in `.env`
> raises `ValidationError` at import and nothing starts — see PROGRESS.md Part 2.

**3. Load the FAQ into Pinecone** (one time)
```powershell
python scripts/create_index.py     # creates the 768-dim index
python scripts/upload_faqs.py      # embeds data/faqs.csv and uploads
```
> Edits to `data/faqs.csv` take effect **only** after re-running `upload_faqs.py`.

**4. Google Sheets** — put the service-account key at `app/credentials/service_account.json`,
create a sheet with header `Timestamp | Name | Phone | Order | Preferred time | Notes`,
and **share it with the service-account email** (Editor). Put its ID in `GOOGLE_SHEETS_ID`.

**5. Run** (two terminals)
```powershell
chcp 65001                                    # UTF-8 console, or Khmer log lines throw
uvicorn app.main:app --reload --port 8000     # Terminal 1 — logs "Agent built (provider=gemini)."
ngrok http 8000                               # Terminal 2 — copy the https URL
```

**6. Wire up Meta — both subscriptions**

This is two separate steps, and missing the second one is the classic failure
(everything looks configured, zero webhooks arrive):

| # | Where | What |
|---|---|---|
| 1 | App Dashboard → **Webhooks** | Callback URL `https://<ngrok-url>/webhook`, Verify token = your `FB_VERIFY_TOKEN`, subscribe the **`messages`** field |
| 2 | App Dashboard → **Messenger → Messenger API Settings** | Connect your Page and **subscribe that Page** to the app |

Step 1 says *"my app is interested in `messages`"*. Step 2 says *"this Page routes
its events to my app."* You need both. See PROGRESS.md Part 3 for the full diagnosis.

> ngrok's free URL changes on every restart — re-paste it into step 1 each time,
> or delivery silently stops.

---

## Configuration (`.env`)

| Variable | Required | Description |
|---|---|---|
| `FB_VERIFY_TOKEN` | ✅ | Any string you invent; must match the value entered in Meta |
| `FB_PAGE_ACCESS_TOKEN` | ✅ | Page Access Token from Messenger settings |
| `LLM_PROVIDER` | ✅ | `gemini` (default) or `openai` |
| `GOOGLE_API_KEY` | ✅* | Gemini key (required when `LLM_PROVIDER=gemini`) — also used for embeddings |
| `OPENAI_API_KEY` | ✅* | Only when `LLM_PROVIDER=openai` |
| `PINECONE_API_KEY` | ✅ | Pinecone key (starts with `pcsk_`) |
| `PINECONE_INDEX_NAME` | – | Vector index name (default `fanpage-faqs`) |
| `GOOGLE_SHEETS_ID` | ✅ | Spreadsheet ID (the part between `/d/` and `/edit`) |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | – | Path to the service-account JSON (default `app/credentials/service_account.json`) |
| `LOG_LEVEL` | – | Logging level (default `INFO`) |

---

## Testing

Three tiers, cheapest first:

| Tier | Command | Covers |
|---|---|---|
| Agent only | `python scripts/local_test.py "What time do you open?"` | LLM, prompt, RAG, Sheets, memory |
| Full loop, faked inbound | `python scripts/fake_webhook.py "What time do you open?"` | + webhook parsing, echo filter, real send to Messenger |
| Real Messenger | message the page | everything, end to end |

`local_test.py` with no arguments starts an interactive session, which is the
easiest way to exercise multi-turn memory and a full booking flow.

> **24-hour messaging window:** the outbound send only succeeds if that PSID
> messaged the page within the last 24h. Error code 10 means it lapsed — message
> the page from that account again and retry.

---

## Branches

| Branch | Contents |
|---|---|
| **`main`** *(default)* | The complete project — full code, all four capabilities |
| `session1` | Echo bot + Session 1 setup guide |
| `session2` | + LangChain agent & memory + Session 2 guide |
| `session3` | + Pinecone RAG + Session 3 guide |
| `session4` | + Google Sheets booking + Session 4 guide |

Each `sessionN` branch is a working checkpoint with its own step-by-step **HTML guide** — handy for teaching or catching up.

---

## Security

- **Never commit secrets.** `.env` and `app/credentials/` are git-ignored — keep tokens and the service-account key out of git.
- **Keep tokens out of logs.** `messenger.py` sends the page token as an
  `Authorization: Bearer` header rather than a query parameter, because httpx
  logs full request URLs at INFO — a token in the querystring ends up printed on
  every reply. `httpx`'s logger is pinned to WARNING in `main.py` for the same reason.
- Page Access Tokens can expire; rotate them if they are ever exposed.
- The app runs in Facebook **Development mode**, which is enough to serve people
  who have a role on the app or page. Serving the general public requires
  publishing the app (Advanced Access `pages_messaging`).

---

## Credits

Capstone for **STEP IT Academy · AI Module 8** — Phnom Penh.
Persona, menu, and FAQ data: *Phnom Penh Noodle House* — replace with your own business to make it yours.
