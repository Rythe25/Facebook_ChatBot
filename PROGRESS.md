# Progress — Refactor: Pet Salon → Local Khmer Noodle Restaurant

**Last updated:** 2026-07-30
**Branch:** `feat/NoodleShop`
**Goal:** Refactor the RAG Messenger chatbot from *Happy Paws Pet Salon* into
*Phnom Penh Noodle House*, a warm, friendly assistant for a local Khmer &
Chinese noodle restaurant.

**Status: DONE. The bot is live on the real Page and verified end-to-end.**
A customer messages the fanpage and the bot replies — in Khmer or English, with
answers grounded in the noodle FAQ data, and bookings written to Google Sheets.
No app publishing was required. See Part 5.

---

## ✅ Part 1 — Content refactor (2026-07-28)

| File | Change |
|---|---|
| `MENU.md` | Rewritten into a detailed, real-style menu — dishes with descriptions, sizes (small/large), soup/dry style, add-ons, drinks, hours, location, contact. Prices in Cambodian riel (៛). |
| `app/prompts.py` | System prompt reworked for the noodle restaurant. **English + Khmer only** (Vietnamese removed). Booking section changed from salon booking → **order / table reservation**. |
| `data/faqs.csv` | All 21 FAQs rewritten for the restaurant (hours, menu, per-dish prices, ingredients, spice, vegetarian, delivery, takeaway, reservations, payment, pork note). Prices match `MENU.md`. |
| `app/tools/sheets.py` | `save_booking`: param `service` → `order`; docstring reworded from "grooming booking / salon" → "order or table reservation / restaurant". No schema change (still name, phone, order, preferred_time, notes). |
| `app/tools/faq_search.py` | `search_faq` docstring updated to describe the restaurant/menu so the agent calls it for menu questions. Retrieval logic unchanged. |

**Restaurant name chosen:** Phnom Penh Noodle House (kept in Phnom Penh / BKK1, like the original data).

---

## ✅ Part 2 — Making it actually run (2026-07-29 → 30)

A runnability audit found the app crashed before the server could start. Four
independent blockers, all now cleared:

| # | Blocker | Symptom | Fix |
|---|---|---|---|
| 1 | `.env` used `GEMINI_API_KEY`, but the field in `config.py` is `google_api_key` | `ValidationError: gemini_api_key — Extra inputs are not permitted` at import; **nothing** ran | renamed the key to `GOOGLE_API_KEY` |
| 2 | Pinecone index `fanpage-faqs` did not exist (account had **zero** indexes) | `404 NOT_FOUND: Resource fanpage-faqs not found` — `faq_search.py` builds the index handle at import, so this killed the agent, webhook and server | ran `scripts/create_index.py` + `scripts/upload_faqs.py` → 21 vectors, dim 768 |
| 3 | `gemini-2.5-flash` is retired for new API keys | `404: This model is no longer available to new users` | `app/agent.py` → `gemini-flash-latest` |
| 4 | Sheet not shared with the service account | `APIError [403]: The caller does not have permission`; `sheets.py` connects at import, so this also blocked startup | shared the sheet with `rythenoodle@localnoodle.iam.gserviceaccount.com` as Editor |

Housekeeping done in the same pass:

| Item | Change |
|---|---|
| `.venv` | Was built from `python3.13t.exe` (free-threaded) and contained only `pip`. Rebuilt from standard Python 3.13 with all four requirement sets installed. |
| `app/config.py` | Placeholder defaults (`google_api_key: str = "GEMINI_API_KEY"`) reverted to `""` — they masked missing config and turned a startup error into a confusing 401 later. Creds path default corrected to `app/credentials/service_account.json`. |
| `.env.example` | Rewritten for all 4 sessions (was session-1 only), documenting the unknown-key crash and the sheet-sharing requirement. |
| `requirements_session4.txt` | **New** — `gspread` was in no requirements file at all. |

---

## 🔍 Part 3 — Live Messenger test: first diagnosis (2026-07-30)

> ⚠️ **The root cause recorded in this section was WRONG.** It is kept as-is
> because the *diagnostic method* was sound and worth reusing — but the actual
> cause was a missing Page-level subscription, not the unpublished app.
> **See Part 5 for the correction.**

Messaged the page from the admin account ("hi", then "Hi"). Both landed in the
Page inbox; the bot never replied. Everything on our side checks out:

| Check | Result |
|---|---|
| `GET /` on :8000 | ✅ `{"status": "ok"}` |
| ngrok tunnel | ✅ `https://swizzle-fried-reenter.ngrok-free.dev` → localhost:8000 |
| Handshake **through the public URL** | ✅ `GET /webhook?hub.challenge=TEST12345` echoed `TEST12345` |
| Page access token | ✅ valid, `expires_at: 0` (never expires), app `Phnom Penh Local Noodle` (`1267375385473375`), scopes `pages_messaging` + `pages_utility_messaging` on page `110644858042565` |
| Message reached the Page | ✅ conversation `t_2246299389465456`, PSID `37429592776655622` |
| Meta dashboard config | ✅ Callback URL saved, `messages` field **Subscribed** (v26.0) |
| **Webhook POSTs Meta actually sent** | ❌ **zero** — ngrok's request log (`http://127.0.0.1:4040/api/requests/http`) shows only our own test GETs |

**Conclusion drawn at the time (incorrect) — the app is unpublished.** The Meta
webhook page states:

> Apps will only be able to receive test webhooks sent from the dashboard while
> the app is unpublished. No production data, **including from app admins,
> developers or testers**, will be delivered unless the app has been published.

That banner is real, but it was **not** what was happening here. The checklist
above has a hole: the "Subscribed" state it verified is the **app-level** webhook
*field* toggle, not the **Page-level** subscription. Both are required, and only
the first was ever confirmed. Correct callback URL + subscribed `messages` field
+ valid token really are necessary-but-not-sufficient — the missing piece was the
Page subscription, not publishing. See Part 5.

### Diagnostic technique worth reusing

`http://127.0.0.1:4040/api/requests/http` is the fastest way to split "Meta isn't
calling us" from "our handler is broken". If that log is empty, no amount of code
debugging helps — the problem is in the Meta dashboard or app mode.

### What was actually missing

The Page-level subscription. See Part 5 — it took one dashboard toggle, and no
publishing at all.

---

## 🗑️ Part 4 — Faked-inbound workaround (2026-07-30, since removed)

Written while Part 3's diagnosis was believed correct. A `scripts/fake_webhook.py`
helper POSTed a Meta-shaped payload straight to `http://127.0.0.1:8000/webhook`,
on the theory that **only the inbound direction was blocked** — the outbound Graph
send works for anyone with a role on the page, so faking the inbound half still
produced a real reply in Messenger.

It worked, but it was solving a problem that did not exist (Part 5). Once real
delivery was fixed, the only thing it uniquely covered — payload parsing, the
`is_echo` filter, and the outbound send — got exercised by every real message
anyway. **Deleted in Part 6.**

### Current testing tiers

| Tier | Command | Covers |
|---|---|---|
| Agent only | `python scripts/local_test.py` | LLM, prompt, RAG, Sheets, memory |
| Real Messenger | message the page | everything, end to end |

`local_test.py` with no arguments is interactive — the easiest way to exercise
multi-turn memory and a full booking flow.

### Gotchas (still current)

- **24-hour messaging window** — the outbound send only succeeds if that PSID
  messaged the page within 24h. Error code 10 / "outside allowed window" means it
  lapsed: message the page from that account again and retry.
- Memory is in-process (`app/memory.py`), so `--reload` restarts wipe conversation
  history mid-test.

---

## ✅ Part 5 — Real Messenger delivery working (2026-07-30)

**Root cause: the Page was never subscribed to the app.** Publishing was never
required. Meta exposes *two* separate subscriptions and they are easy to
conflate:

| # | Where | Means | Verified in Part 3? |
|---|---|---|---|
| 1 | App Dashboard → **Webhooks** → `messages` toggle | "my app is interested in `messages` events" | ✅ yes |
| 2 | App Dashboard → **Messenger → Messenger API Settings** → per-Page subscription | "**this Page** routes its events to my app" | ❌ **never checked** |

Only #1 was ever confirmed. Without #2, Meta has no route from the Page to the
app and drops the event before app-mode is even relevant — which is exactly why
the tunnel log stayed empty and looked identical to the unpublished-app symptom.

The programmatic check needs a scope the original token lacked:

```
GET /{page-id}/subscribed_apps
-> 403 (#200) Requires pages_manage_metadata permission
```

Fixed by subscribing the Page in the dashboard and regenerating the token.

### Second bug, found immediately after

With delivery fixed, Meta's POSTs started arriving — as `502 Bad Gateway`.
ngrok's tunnel was healthy; **uvicorn was simply not running**. `ngrok http 8000`
happily stays up with nothing behind it, and a dead server is indistinguishable
from a misconfigured one if you only look at the Meta side.

Order of checks that works, cheapest first:

1. `curl http://127.0.0.1:8000/` — is the app even up?
2. `curl http://127.0.0.1:4040/api/tunnels` — is ngrok pointed at the right port?
3. `curl https://<ngrok>/webhook?hub.mode=subscribe&hub.verify_token=x&hub.challenge=PING`
   — a `403 Verification failed` is a **success** signal here: it proves the
   request reached our handler.
4. `GET /me` with the page token — catches a stale token before it shows up as a
   silent send failure.

### Third fix — token was leaking into the logs

`messenger.py` sent the page access token as a **query parameter**, and httpx
logs full request URLs at INFO, so every reply printed the live token to the
console:

```
INFO:httpx:HTTP Request: POST .../me/messages?access_token=EAASAq9Ol8V8BS...
```

Now sent as an `Authorization: Bearer` header, and `httpx`'s logger is pinned to
WARNING in `main.py`. Verified the Graph API accepts Bearer auth (`GET /me` → 200).

⚠️ **The already-printed token still needs rotating.** The fix stops future
leaks; it does not un-leak the token that was written to the console before it.

### Confirmed working

Server log from the real Page conversation — no mocks, no `fake_webhook.py`:

```
Message from 37429592776655622: Hello                     -> Sent reply
Message from 37429592776655622: When is the opening time  -> Pinecone top_k=3 -> Sent reply
Message from 37429592776655622: អ្នកមានស៊ុបប្រភេទណាខ្លះ?       -> Pinecone x3      -> Sent reply
POST /webhook HTTP/1.1" 200 OK
```

English, Khmer, and RAG retrieval all confirmed over real Messenger delivery.

---

## 🧹 Part 6 — Cleanup (2026-07-30)

| File | Change |
|---|---|
| `requirements.txt` | Consolidated all four session files into one |
| `requirements_session{2,3,4}.txt` | Deleted — merged above |
| `HOW_TO.md` | Deleted — speculative and partly wrong ("inferred from the structure"); README covers setup properly |
| `INSTRUCTION.md` | Deleted — the refactor brief; work complete |
| `README.md` | Rewritten — still described *Happy Paws Pet Salon*. Now documents the noodle shop, the correct model (`gemini-flash-latest`), the single requirements file, and **both** Meta subscription steps |
| `app/messenger.py` | Token moved from query param to `Authorization` header |
| `app/main.py` | `httpx` logger pinned to WARNING; removed stale `TODO (Session 2)` (done by `lifespan`) |
| `app/memory.py` | Removed `clear_history()` — never called |
| `scripts/fake_webhook.py` | Deleted — a workaround for a problem that turned out not to exist (Part 4) |

`docs/` (PRD, ARCHITECTURE, SPRINT_PLAN) left untouched — course scaffolding, not app docs.

---

## ✅ Part 7 — Order type recorded in the sheet (2026-07-30)

Bookings were saved without distinguishing how the customer wanted the food, so
a delivery and a dine-in reservation looked identical in the sheet.

| File | Change |
|---|---|
| `app/tools/sheets.py` | `save_booking` takes `order_type` ("Dine-in" / "Takeaway" / "Delivery"), written as a new 4th column. Logs the save. |
| `app/prompts.py` | Agent works out the order type, asks for a delivery address, and records **only after the customer confirms** |

Spreadsheet **Local Noodle**, tab **Sheet1** (the code uses `.sheet1`, the first
tab by position, so its name doesn't matter). Columns are now:

```
Timestamp | Name | Phone | Order type | Order | Preferred time | Notes
```

Verified live — `scripts/local_test.py` with a one-shot delivery order wrote:

```
2026-07-30 23:11:58 | Dara | 011 222 333 | Delivery | 2 Special Noodle | Tomorrow at 7pm | Delivery address: St. 302 BKK1, no chili
```

The agent inferred `Delivery` and moved the address into notes unprompted.

⚠️ The old `Sokha` test row predates this column, so its `Order` value sits in
the `Order type` cell. Delete it (and add the header row) when convenient.

---

## 📦 Part 8 — Repo polish and publish (2026-07-30)

Final pass to make the project presentable as a public GitHub repository.

| File | Change |
|---|---|
| `README.md` | Rewritten as the repo landing page — badges, feature table, architecture diagram, six-step setup with every Meta click spelled out, config reference, a collapsible **Troubleshooting** section built from the real failures in Parts 2–5, and a customisation guide |
| `.gitignore` | Removed a duplicate `credentials/` entry; added `*.log`, `ngrok.yml`, `ngrok.exe`, `*.json.bak` |
| `.env.example` | Comments moved onto their own lines — a trailing `# ...` after a value is easy to paste over and hard to debug |
| `app/agent.py` | Removed a stale `# Session 3-4: add tools=...` comment referring to a tool name that no longer exists |

Verified before pushing: `git ls-files` contains no `.env`, no `credentials/`,
no `__pycache__`, and no `.venv` — only source, data, docs and config.

**Published to** <https://github.com/Rythe25/Facebook_ChatBot> — `feat/NoodleShop`
pushed as `main`. The target repo previously held a single "Initial commit" with
a stub `README.md` and unrelated history, so the push replaced it.

---

## 🧪 Verification (all live calls, nothing mocked)

```
GET /                              -> 200 {"status": "ok"}
GET /webhook  (correct token)      -> 200 echoes hub.challenge
GET /webhook  (wrong token)        -> 403 Verification failed

"What time do you open?"           -> 7:00 AM – 9:00 PM daily            (RAG hit)
"How much is the special noodle?"  -> 15,000 riel / 16,000 large         (matches MENU.md)
"សួស្តីបង តើហាងលក់មីអីខ្លះ?"          -> full Khmer reply, Khmer numerals    (language rule holds)
3-turn pre-order (Sokha)           -> row written to "Local Noodle" Sheet1:
   2026-07-30 00:09:33 | Sokha | 012 888 999 | 2 bowls of Special Noodle |
   Tomorrow at 6:00 PM | Pickup. No chili please.
```

The booking test correctly assembled details spread across three messages
(order + time from turn 2, name + phone + "no chili" from turn 3).

---

## 🧠 How the FAQ RAG works (reference)

`faqs.csv` stores **both**, split by column:
- **`answer` = source of truth** — the factual content the bot speaks from. Embedded + uploaded to Pinecone, returned to the agent at query time.
- **`question` = sample phrasings** — embedded so real customer messages match semantically (paraphrases / Khmer equivalents still match the row).

Runtime: `search_faq` embeds the customer message → Pinecone query (top_k=3, score ≥ 0.5) → returns matching `question`+`answer` to the agent.

Implication: anything the bot must factually know **must** live in `faqs.csv`, and edits take effect **only after re-running `scripts/upload_faqs.py`**.

---

## ▶️ How to run

```powershell
.venv\Scripts\activate
chcp 65001                                    # UTF-8 console, or Khmer log lines throw
uvicorn app.main:app --reload --port 8000     # terminal 1
ngrok http 8000                               # terminal 2 → copy the https URL
```

Meta dashboard → app **Phnom Penh Local Noodle** — **both** of these:
1. **Webhooks** → Callback URL `https://<ngrok>.ngrok-free.dev/webhook`,
   Verify token = `FB_VERIFY_TOKEN` from `.env`, subscribe the **messages** field
2. **Messenger → Messenger API Settings** → subscribe the **Page** to the app

Notes: ngrok's free URL changes on every restart (re-paste it into step 1 each
time — delivery silently stops otherwise). The app does **not** need to be
published; Development mode delivers fine once step 2 is done (Part 5).

**To just test the agent, skip all of the above** (no ngrok, no Meta dashboard):

```powershell
python scripts/local_test.py "What time do you open?"   # one-shot
python scripts/local_test.py                            # interactive, tests memory
```

---

## ⏭️ Next steps / TODO

- [x] **`README.md`** rewritten for the noodle shop (Part 6).
- [x] Real Messenger delivery working end-to-end (Part 5).
- [x] Page access token no longer leaked into logs (Part 5).
- [ ] **Rotate `FB_PAGE_ACCESS_TOKEN`** — the pre-fix token was printed to the console (Part 5).
- [ ] Optional: reserve ngrok's free static domain so the Callback URL stops changing on every restart.
- [ ] Optional: add a header row to the sheet (`Timestamp | Name | Phone | Order | Preferred time | Notes`) and delete the "Sokha" test row.
- [ ] Optional hardening: `sheets.py` and `faq_search.py` connect at **import time**, so any external misconfiguration takes down the whole server instead of degrading one tool. Lazy-connect on first use would keep chat + FAQ alive when Sheets is down.

---

## 📋 Commit history on this branch

- **2026-07-30** — Parts 1–3 committed on `feat/NoodleShop`: content refactor, runnability fixes, and this progress log.
- **2026-07-30** — Parts 5–6: real Messenger delivery fixed (Page subscription), token leak closed, project cleaned up, README rewritten.

(`.env` and `app/credentials/` stay gitignored — they hold the real keys.)
