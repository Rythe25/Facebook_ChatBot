# Happy Paws — Fanpage Chatbot 🐾

An AI customer-service chatbot for a **Facebook Messenger** fanpage (persona: *Happy Paws Pet Salon*).
It chats with customers, answers questions from a **real FAQ knowledge base**, and **books appointments straight into Google Sheets** — no hallucinated prices or hours.

> Capstone project for *Creating AI Applications Using Python* (Module 8) — **STEP IT Academy, Phnom Penh**.
> Built in four sessions: **Speak → Think → Know → Act**.

---

## What it does

| Capability | How |
|---|---|
| 🗣️ **Speak** | Receives every message via a FastAPI webhook and replies through the Facebook Graph API |
| 🧠 **Think** | A LangChain agent (Gemini or OpenAI) with **per-customer conversation memory** |
| 📚 **Know** | Answers FAQs via **Pinecone RAG** — grounded in your real data, never invented |
| ✅ **Act** | Collects a booking (name · phone · service · time) and appends a row to **Google Sheets** |

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
         FAQ question?   "book / save"?     normal chat
      search_faq→Pinecone  save_booking→Sheet   LLM answers
              └───────────────┼────────────────┘
                              ▼
                     messenger.py sends the reply ─▶ Customer  (+ memory updated)
```

---

## Tech stack

- **Web:** FastAPI + Uvicorn
- **LLM:** Google Gemini (`gemini-2.5-flash`, default) or OpenAI — switchable by env var
- **Agent:** LangChain (`create_agent`)
- **Memory:** in-memory, keyed by Facebook PSID (resets on restart — by design)
- **Knowledge (RAG):** Pinecone + Gemini embeddings (768-dim, cosine)
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
  prompts.py         system prompt (persona + hard rules)
  tools/
    faq_search.py    @tool search_faq — Pinecone retrieval
    sheets.py        @tool save_booking — append a row to Google Sheets
data/faqs.csv        FAQ knowledge base (question,answer)
scripts/
  create_index.py    create the Pinecone index (run once)
  upload_faqs.py     embed faqs.csv and upsert to Pinecone (run once)
  local_test.py      chat with the agent from the terminal (no Facebook needed)
docs/                PRD.md, ARCHITECTURE.md, SPRINT_PLAN.md
credentials/         Google service-account.json (git-ignored — never committed)
```

---

## Prerequisites

- **Python 3.11 or 3.12** (not 3.13 / 3.14 — some libraries have no prebuilt wheel yet)
- A Facebook account + a test **fanpage** you are admin of, and a Facebook App with the **Messenger** product
- A **Google AI Studio** API key (free — for Gemini)
- A **Pinecone** account (free Starter tier)
- A **Google Cloud** service account with **Sheets + Drive API** enabled, and a Google Sheet shared with it
- **ngrok** (free account) for local HTTPS

---

## Setup

**1. Create the virtual environment and install dependencies**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1                 # prompt should show (.venv)
python -m pip install --upgrade pip
pip install -r requirements.txt              # Session 1
pip install -r requirements_session2.txt     # LangChain + Gemini
pip install -r requirements_session3.txt     # Pinecone
pip install gspread                           # Session 4 — Google Sheets
```
> Every new terminal: **activate the venv first** (`.\.venv\Scripts\Activate.ps1`).

**2. Configure `.env`** (copy the template, then fill in the values below)
```powershell
Copy-Item .env.example .env
```

**3. Load the FAQ into Pinecone** (one time)
```powershell
python scripts/create_index.py     # creates the 768-dim index
python scripts/upload_faqs.py      # embeds data/faqs.csv and uploads
```

**4. Google Sheets** — put the service-account key at `credentials/service-account.json`,
create a sheet with header `Timestamp | Name | Phone | Service | Preferred time | Notes`,
and **share it with the service-account email** (Editor). Put its ID in `GOOGLE_SHEETS_ID`.

**5. Run** (two terminals)
```powershell
uvicorn app.main:app --reload      # Terminal 1 — log should print "Agent built (provider=gemini)."
ngrok http 8000                    # Terminal 2 — copy the https URL
```
Then register the webhook in Meta: **Callback URL** = `https://<ngrok-url>/webhook`,
**Verify token** = your `FB_VERIFY_TOKEN`, and subscribe the **`messages`** field only.

> 📘 **Full step-by-step guides** (with screenshots) live on the session branches — see [Branches](#branches).

---

## Configuration (`.env`)

| Variable | Required | Description |
|---|---|---|
| `FB_VERIFY_TOKEN` | ✅ | Any string you invent; must match the value entered in Meta |
| `FB_PAGE_ACCESS_TOKEN` | ✅ | Page Access Token (from the Messenger settings; extend to 60 days) |
| `LLM_PROVIDER` | ✅ | `gemini` (default) or `openai` |
| `GOOGLE_API_KEY` | ✅* | Gemini key (required when `LLM_PROVIDER=gemini`) — also used for embeddings |
| `OPENAI_API_KEY` | ✅* | Only when `LLM_PROVIDER=openai` |
| `PINECONE_API_KEY` | ✅ | Pinecone key (starts with `pcsk_`) |
| `PINECONE_INDEX_NAME` | – | Vector index name (default `fanpage-faqs`) |
| `GOOGLE_SHEETS_ID` | ✅ | Spreadsheet ID (the part between `/d/` and `/edit`) |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | – | Path to the service-account JSON (default `./credentials/service-account.json`) |
| `LOG_LEVEL` | – | Logging level (default `INFO`) |

---

## Testing

Talk to the agent straight from the terminal — no ngrok, no Messenger:
```powershell
python scripts/local_test.py "What time do you open on weekdays?"   # one-shot
python scripts/local_test.py                                        # interactive (tests memory)
```
A booking with all four details in one message writes a real row to your sheet. Then test live on Messenger (as the page admin).

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

- **Never commit secrets.** `.env` and `credentials/` are git-ignored — keep tokens and the service-account key out of git.
- Page Access Tokens expire (extend to 60 days); rotate keys if they are ever exposed.
- The app runs in Facebook **Development mode** — it only replies to admins of the test page. Serving real customers requires Meta App Review.

---

## Credits

Capstone for **STEP IT Academy · AI Module 8** — Phnom Penh.
Persona, FAQ data, and fanpage: *Happy Paws Pet Salon* — replace with your own business to make it yours.

<!-- TODO: add your live fanpage URL and a one-line persona description here before submitting. -->
