# Progress — Refactor: Pet Salon → Local Khmer Noodle Restaurant

**Last updated:** 2026-07-30
**Branch:** `feat/NoodleShop`
**Goal:** Refactor the RAG Messenger chatbot from *Happy Paws Pet Salon* into
*Phnom Penh Noodle House*, a warm, friendly assistant for a local Khmer &
Chinese noodle restaurant. (Source: `INSTRUCTION.md`)

**Status: the bot runs and is verified end-to-end.** Server boots, FAQ retrieval
answers from the noodle data, Khmer/English switching works, and a booking writes
a real row to Google Sheets. Remaining work is cosmetic (README) plus the live
Messenger test, which is **blocked on Meta, not on our code** — see Part 3.

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

## 🔍 Part 3 — Live Messenger test: diagnosed, blocked on Meta (2026-07-30)

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

**Root cause — the app is unpublished.** The Meta webhook page states it plainly:

> Apps will only be able to receive test webhooks sent from the dashboard while
> the app is unpublished. No production data, **including from app admins,
> developers or testers**, will be delivered unless the app has been published.

This is a *change* from the old behaviour that Session 1 notes (and this file's
"How to run" section) assumed — development mode used to deliver messages from
app admins/testers. It no longer does for Messenger. Correct callback URL +
subscribed `messages` field + valid token are all necessary but **not sufficient**.

### Diagnostic technique worth reusing

`http://127.0.0.1:4040/api/requests/http` is the fastest way to split "Meta isn't
calling us" from "our handler is broken". If that log is empty, no amount of code
debugging helps — the problem is in the Meta dashboard or app mode.

### To unblock

1. **Test button** next to `messages` on the Webhooks page — Meta POSTs a sample
   payload even while unpublished. Proves the server → agent path end-to-end.
   (`send_message` will fail on the fake sample PSID; that is expected.)
2. **Publish the app**: App Dashboard → toggle **Development → Live**. Requires
   App Settings → Basic to have a Privacy Policy URL, an app category, and
   usually a 1024×1024 icon. No App Review / Business Verification needed to
   message a page you have a role on — Standard Access `pages_messaging` covers
   admins/testers; Advanced Access is only for the general public.
3. Message the page again → expect `POST /webhook` + `Incoming webhook payload`.

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

Meta dashboard → app **LocalNoodle** → Messenger → Webhooks:
- Callback URL: `https://<ngrok>.ngrok-free.app/webhook`
- Verify token: value of `FB_VERIFY_TOKEN` in `.env`
- Subscribe the page to the **messages** field

Notes: ngrok's free URL changes on every restart (re-paste it into Meta each
time — delivery silently stops otherwise), and the app **must be published /
Live** or Meta delivers nothing at all, admins included (see Part 3).

---

## ⏭️ Next steps / TODO

- [ ] **Publish the app (Development → Live)** — the one blocker for the live Messenger test. Needs a Privacy Policy URL + app category first.
- [ ] **Live Messenger test** — after publishing: server + tunnel up, message the page, expect `POST /webhook`.
- [ ] **`README.md` still describes Happy Paws Pet Salon** — the only file not refactored.
- [ ] Optional: reserve ngrok's free static domain so the Callback URL stops changing on every restart.
- [ ] Optional: add a header row to the sheet (`Timestamp | Name | Phone | Order | Preferred time | Notes`) and delete the "Sokha" test row.
- [ ] Optional hardening: `sheets.py` and `faq_search.py` connect at **import time**, so any external misconfiguration takes down the whole server instead of degrading one tool. Lazy-connect on first use would keep chat + FAQ alive when Sheets is down.

---

## 📋 Commit history on this branch

- **2026-07-30** — Parts 1–3 committed on `feat/NoodleShop`: content refactor, runnability fixes, and this progress log.

(`.env` and `app/credentials/` stay gitignored — they hold the real keys.)
