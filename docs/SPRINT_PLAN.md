# 4-Session Sprint Plan

## Pedagogy

**I Do / We Do / You Do** progression, with the balance shifting toward "You Do" over the four sessions. Each session ends with a working artifact committed to a checkpoint branch — the safety net for students who fall behind in this intensive solo format.

---

## Session 1 — Foundation + Echo Bot

**Theme:** Get a Python webhook to talk to Facebook end-to-end.

**Pedagogy mix:** ~70% I Do, 30% We Do.

**Duration:** 2.5 hours.

### Setup (instructor demo, ~30 min)

- Create Facebook app + own test fanpage (each student does this in parallel)
- Generate Page Access Token, extend to 60 days
- Install ngrok, get free static URL
- Configure webhook URL + verify token in Meta dashboard
- Add tokens to `.env`

### Code written together (~75 min)

- `app/main.py` — FastAPI factory + router wiring
- `app/config.py` — pydantic-settings, all env vars in one place
- `app/webhook.py` — `GET /webhook` (verify) + `POST /webhook` (receive + echo)
- `app/messenger.py` — `send_message()` via Graph API

### Demo at end of session (~15 min)

Student sends "hello" on their own fanpage → bot replies "hello". Live, on a real fanpage.

This is a deliberate psychological milestone — students see the bot **actually running on their own Facebook page**, not on `localhost`. Motivation for the rest of the course.

### Checkpoint branch: `checkpoint-1`

### Homework before Session 2

- Get the echo bot fully working on own fanpage (if not finished in class)
- Read 30-min FastAPI async basics tutorial
- Sign up for **either** OpenAI **or** Gemini API key (Gemini recommended)
- Read `docs/ARCHITECTURE.md#common-pitfalls` items 1, 2, 3

---

## Session 2 — Brain (Agent + Memory)

**Theme:** Replace echo with a real conversational AI that remembers context.

**Pedagogy mix:** 50% I Do, 50% We Do.

**Duration:** 2.5 hours.

### Concepts (instructor explains, ~20 min)

- LangChain agent vs. raw LLM call
- System prompts and bot persona design
- Why memory matters; trade-off of in-memory vs. persistent storage
- Multi-provider abstraction pattern

### Code written together (~90 min)

- `app/agent.py` — provider switch (OpenAI / Gemini), agent factory using `create_tool_calling_agent`
- `app/memory.py` — `dict[str, ChatMessageHistory]` keyed by Facebook PSID
- `app/prompts.py` — system prompt with bot persona, hard rules (no leaking internal logic)
- Wire agent into `webhook.py` (replace echo logic)

### Demo at end (~15 min)

Multi-turn conversation. Bot answers "what's your name?" → student says "my name is X" → bot uses it later. Memory works.

### Checkpoint branch: `checkpoint-2`

### Homework before Session 3

- Sign up for Pinecone (require phone OTP in some regions — **do this immediately**, not the day of Session 3)
- Prepare own FAQ dataset: at least 10 Q&A pairs in `data/faqs.csv` (columns: `question`, `answer`)
- Decide on bot persona (pet salon? restaurant? bookstore? Pick something with concrete FAQs)
- Read `docs/ARCHITECTURE.md#common-pitfalls` items 4, 5, 8

---

## Session 3 — Knowledge (Pinecone RAG Tool)

**Theme:** Bot answers from a knowledge base, not from the LLM's generic memory.

**Pedagogy mix:** 50% We Do, 50% You Do.

**Duration:** 2.5 hours.

### Concepts (quick review from Module 8, ~15 min)

- Embedding model dimensions — why they matter
- Vector similarity search vs. keyword search
- Why RAG beats stuffing all FAQs into the system prompt (token cost, context limits)

### Code written together (~50 min)

- `scripts/upload_faqs.py` — read CSV, embed each row, upsert to Pinecone (run once)
- `app/tools/faq_search.py` — `@tool` decorated function wrapping Pinecone query
- Attach the tool to the agent
- Update system prompt to mention the tool

### Students do on their own (~60 min)

- Upload their own FAQs to Pinecone
- Test queries that **should** match (questions clearly in the FAQ)
- Test queries that **shouldn't** match (random questions outside scope)
- Tune `top_k` and similarity threshold

### Demo at end (~15 min)

Bot answers business-specific questions ("what time do you close?", "how much is dog grooming?") from FAQ data, not from generic LLM knowledge. Students compare answers before/after RAG.

### Checkpoint branch: `checkpoint-3`

### Homework before Session 4

- Polish system prompt (eliminate any "internal logic leaks")
- Create a Google service account + share a sheet with the service account email
- Write **3 demo scenarios** for demo day (e.g., "ask about a price", "ask about hours", "make a booking")
- Read `docs/ARCHITECTURE.md#common-pitfalls` item 9

---

## Session 4 — Action + Demo Day

**Theme:** The bot doesn't just answer — it takes action.

**Pedagogy mix:** 30% We Do (the tool), 70% You Do (polish + demo).

**Duration:** 2.5 hours.

### Code written together (~45 min)

- `app/tools/sheets.py` — `@tool` decorated function using `gspread` to append a row
- Choose **one** scenario (instructor picks before class): save customer info **or** book appointment
- Update system prompt to describe when to call the tool

### Students do (~45 min)

- Integrate the tool with their agent
- Test the full happy path: customer asks question → bot answers → customer says "I want to book" → bot collects info → bot writes to Sheet
- Fix their own bugs (instructor circulates, helps unblock — Socratic style, hints first)

### Demo day (~60 min, ~5 min per student × ~12 students)

Each student demonstrates on their own fanpage:

1. Ask 1 FAQ question (RAG path)
2. Ask 1 question OUTSIDE the FAQ (gracefully degrade)
3. Trigger the Sheets action
4. Show the resulting row in their Google Sheet

Instructor evaluates per rubric in real time.

### Final deliverable on `main` branch

- Working bot
- Updated README (with the student's own fanpage URL and persona description)
- Recorded 1-2 min demo video (optional bonus: 5 points on rubric)

---

## Checkpoint Recovery

If a student falls behind (e.g., loses a day to FB App config issues), they can:

```bash
git checkout checkpoint-N
```

…to jump to the start of Session N+1. They lose the personalization they had, but they don't lose the course.

This is the safety net for solo intensive format — without it, one bad day cascades and students drop out.

## Time Buffer

Total class time: 4 × 2.5h = 10h. Real talk: ~10% of this gets eaten by ngrok URL changes, Facebook account oddities, and Pinecone signup issues. Budget for ~9h of effective teaching time. If you have 3h sessions instead of 2.5h, the extra 30 min per session goes into student debugging time, not new material.
