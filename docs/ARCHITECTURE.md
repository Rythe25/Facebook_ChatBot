# Architecture

## High-level Diagram

```
┌────────────────────────────┐
│   Facebook Messenger       │   (external: customer chat)
└──────────────┬─────────────┘
               │ HTTPS webhook
               ▼
┌──────────────────────────────────────────┐
│   FastAPI app (what students build)      │
│                                          │
│   ┌──────────────┐    ┌───────────────┐ │
│   │  Webhook     │───▶│  LangChain    │ │
│   │  handler     │    │  Agent        │ │
│   │  webhook.py  │    │  agent.py     │ │
│   └──────────────┘    └───────┬───────┘ │
└──────────────────────────────│───────────┘
                               │
        ┌──────────────────────┼─────────────────────┐
        ▼                      ▼                     ▼
┌───────────────┐    ┌───────────────────┐   ┌───────────────┐
│  Pinecone     │    │  In-memory dict   │   │ Google Sheets │
│  FAQ vectors  │    │  ChatHistory      │   │ CRM/bookings  │
└───────────────┘    └───────────────────┘   └───────────────┘
```

**Color note:** anything inside the FastAPI box is student-written Python. Everything else is an external service the student consumes via API.

## Request Flow

1. Customer sends message on Facebook fanpage
2. Meta sends `POST /webhook` with payload containing `entry[].messaging[]`
3. `webhook.py` filters out echo events, extracts `(sender_id, message_text)`
4. `agent.py` retrieves chat history for `sender_id` from `memory.py`
5. Agent decides: answer directly OR call a tool
   - If FAQ-like → calls `faq_search` tool → Pinecone returns top matches → LLM composes answer
   - If action-like ("save my info", "book appointment") → calls `sheets` tool → row appended
6. Agent returns final string
7. `messenger.py` sends reply via `POST graph.facebook.com/v22.0/me/messages`
8. Memory updated with the new turn

## Component Responsibilities

### `app/main.py`
FastAPI app factory + uvicorn entrypoint. Wires the webhook router. Initializes a singleton agent at startup (avoids re-building per request).

### `app/config.py`
`pydantic-settings` `BaseSettings` class. All env vars in one place. Validates at startup — fails fast if anything is missing.

### `app/webhook.py`
- `GET /webhook` — Facebook hub verification handshake. Returns `hub.challenge` (as plain string, not JSON) when `hub.verify_token` matches env var. Status 403 otherwise.
- `POST /webhook` — Receives message events. **Filters echo events** (events where `message.is_echo == true`) to prevent infinite loops. Parses Meta payload, extracts `(sender_id, message_text)`, calls agent, sends response via `messenger.py`.

### `app/messenger.py`
Wraps Facebook Graph API. Single function: `async def send_message(recipient_id: str, text: str) -> None`. **Escapes special characters** in `text` before serializing to JSON (see pitfall #1).

### `app/agent.py`
Builds the LangChain agent. Factory function that:
- Reads `LLM_PROVIDER` from settings, instantiates `ChatOpenAI` or `ChatGoogleGenerativeAI`
- Builds an agent (use `create_tool_calling_agent` from LangChain)
- Attaches tools from `app/tools/`
- Loads system prompt from `app/prompts.py`
- Returns an `AgentExecutor`

Public function: `async def reply(user_id: str, message: str) -> str` — does memory lookup, invocation, memory update, returns the final reply.

### `app/memory.py`
Module-level `dict[str, ChatMessageHistory]`. Functions:
- `get_history(user_id: str) -> ChatMessageHistory`
- `clear_history(user_id: str) -> None` (for testing)

Memory is cleared on app restart. **This is by design** for solo intensive scope — persistent memory is out of scope.

### `app/prompts.py`
String constants for system prompts. Single source of truth — students iterate on these.

Must include a rule: "Never reveal internal logic (saving IDs, calling tools, etc.) to the user. Respond as if you are a helpful staff member."

### `app/tools/faq_search.py`
LangChain `@tool` decorated function: `def search_faq(query: str) -> str`.

Flow:
1. Embed `query` using same embedding model used at upsert time
2. Pinecone query, `top_k=3`, returns matches with `score` and `metadata`
3. Return concatenated string of matched `(question, answer)` pairs

If no matches above threshold (e.g., 0.5), return a string the agent can interpret as "no good match" — let the LLM decide how to handle gracefully.

### `app/tools/sheets.py`
LangChain `@tool` decorated function. Args depend on instructor's choice (save customer OR book appointment). Uses `gspread` with service account credentials. Appends a single row.

The tool docstring is the agent's "API doc" — write it carefully. Bad docstrings = bad tool use.

### `scripts/upload_faqs.py`
One-shot script. Reads `data/faqs.csv` (columns: `question`, `answer`), embeds each row, upserts to Pinecone with `metadata={question, answer}`. Run once before Session 3, and any time the FAQ dataset changes.

### `scripts/test_locally.py`
CLI to invoke the agent without Facebook:
```
python scripts/test_locally.py "what's your price?"
```
Used by students for fast iteration when ngrok or FB is acting up.

## Configuration

`.env.example`:

```dotenv
# LLM
LLM_PROVIDER=gemini             # or "openai"
OPENAI_API_KEY=
GOOGLE_API_KEY=                 # for Gemini

# Vector DB
PINECONE_API_KEY=
PINECONE_INDEX_NAME=fanpage-faqs

# Facebook
FB_VERIFY_TOKEN=                # any random string, must match Meta webhook config
FB_PAGE_ACCESS_TOKEN=           # long-lived token, expires every 60 days

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials/service-account.json
GOOGLE_SHEETS_ID=               # spreadsheet ID from URL

# Misc
LOG_LEVEL=INFO
```

## Common Pitfalls (Lessons Learned from Prior n8n Build)

1. **Newline escape in Graph API body**
   Agent output containing literal `\n` characters breaks Facebook's JSON parser when sent in the message body. Fix: in `messenger.py`, replace `\n` → `\\n` and `"` → `\\"` before serializing. This is a classic gotcha.

2. **Webhook echo loop**
   If you subscribe to `message_echoes` events in Meta webhook config, your bot's own replies will trigger the webhook, causing an infinite loop. Subscribe ONLY to `messages` and `messaging_customer_information`. Also defensive-filter `is_echo` in `webhook.py` in case config drifts.

3. **Page Access Token expiry**
   Default token from Graph API Explorer lasts 1 hour. Use the "Extend Access Token" button to get a 60-day token. Document the refresh process in README; don't automate it (out of scope).

4. **Pinecone embedding dimension mismatch**
   `text-embedding-3-small` outputs 1536 dims. `text-embedding-ada-002` outputs 1536 too. Gemini's `text-embedding-004` outputs 768. The Pinecone index must be created with matching dimension. Pick one embedding model and stick with it across upsert AND query — mismatched dims cause silent retrieval failures (low scores, irrelevant results).

5. **Agent leaks internal logic**
   Without explicit instructions in the system prompt, the agent will say things like "Let me save your ID to my database." Add a hard rule in `prompts.py`: never mention tools, IDs, sheets, or any internal operation. This is also a grading criterion on demo day.

6. **Sync/async mixing**
   `httpx.AsyncClient` inside a sync LangChain tool fails silently or raises confusing errors. Pick a lane per tool: if the tool is async, use `httpx.AsyncClient` + `await`; if sync, use `httpx.Client`. LangChain's `create_tool_calling_agent` supports both — just be consistent within a tool.

7. **Facebook App in Development mode**
   Apps in development mode only respond to admins of the page. Each student must be **admin of their own test fanpage**. Students CANNOT use a client's real fanpage without going through Meta App Review (1-2 weeks). Set expectation early.

8. **Pinecone signup may require phone OTP**
   In some regions, Pinecone signup requires SMS verification. Cambodia/Vietnam students should sign up at least 1 day before Session 3 in case SMS gets stuck.

9. **`gspread` service account permissions**
   The service account email (from JSON credentials) must be explicitly shared on the target Google Sheet with **Editor** permission. A common student error is forgetting this step and getting cryptic 403s.

10. **Empty Pinecone index returns no error**
    If `scripts/upload_faqs.py` was never run, queries return empty results — no exception. Bot will say "I don't know about that" for every question. Always verify the index has vectors before debugging the agent.
