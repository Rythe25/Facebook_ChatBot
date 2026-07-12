# Product Requirements: Fanpage Chatbot Capstone

## Context

- **Course:** Creating AI Applications Using Python (Module 8 capstone)
- **Institution:** STEP IT Academy, Phnom Penh
- **Format:** 4-session intensive, solo project
- **Duration:** ~10 hours class + ~10 hours homework
- **Audience:** Students who completed Module 8 (RAG, embeddings, LangChain basics, vector DBs)

## Problem Statement

Students have learned RAG, vector databases, and LangChain in isolation. The capstone integrates these into a deployed product that interacts with **real users via Facebook Messenger** — not a toy demo with mocked inputs.

## What Students Build

A Python service that:

1. Receives messages from a Facebook fanpage via webhook
2. Routes them to a LangChain agent
3. The agent uses a Pinecone-backed RAG tool to answer FAQ questions
4. The agent uses a Google Sheets tool to save customer info OR book appointments (instructor picks one)
5. Replies back to the customer via Facebook Graph API

## In Scope

- FastAPI webhook handler (GET verify + POST receive)
- Multi-provider LLM (OpenAI or Gemini, switched by env var)
- LangChain agent with system prompt and conversation memory
- In-memory chat memory keyed by Facebook PSID (page-scoped ID)
- RAG tool: search FAQ from Pinecone (FAQ data lives in `data/faqs.csv`)
- One Sheets tool: append a row when the agent decides to
- ngrok tunnel for local HTTPS
- README + `.env.example` + setup guide

## Out of Scope (Optional Bonuses Only)

- Postgres-backed memory
- Telegram notifications
- Docker / docker-compose
- X-Hub-Signature webhook signature verification
- Multi-tenancy (multiple fanpages on one instance)
- Token refresh automation
- Production deployment (Cloud Run, Fly, etc.)

These are deliberately out of scope to keep the project completable in 4 intensive sessions. Students who finish early may attempt them as bonuses.

## Learning Outcomes

Each student, by end of capstone, can:

1. Build a FastAPI webhook server that handshakes with an external platform
2. Configure a LangChain agent with custom tools and system prompts
3. Implement a RAG pipeline end-to-end (embed → upsert → retrieve → use in prompt)
4. Wire AI logic to a real-world output channel (Google Sheets)
5. Debug an async Python service that talks to 3+ external APIs
6. Explain trade-offs between OpenAI and Gemini for a specific use case

## Success Criteria

A passing capstone has:

- ✅ Bot runs on student's own test fanpage (verified live during demo day)
- ✅ Bot answers at least 5 FAQ questions correctly via RAG (not from LLM generic knowledge)
- ✅ Bot writes to Google Sheets when the conversation triggers it
- ✅ README documents setup steps clearly (instructor or another student can follow it)
- ✅ No hardcoded secrets in code (all via `.env`)
- ✅ Code runs without crashing for a 5-turn conversation

## Non-functional Requirements

- **Latency:** ≤ 8 seconds from user message to bot reply (RAG + LLM combined). Not optimized further.
- **Reliability:** Survives a typo or malformed user input without crashing.
- **Observability:** Logs each incoming message, agent decision, and outgoing reply at INFO level. Students must be able to debug by reading logs.

## Pedagogical Principles

- **I Do → We Do → You Do** progression across the 4 sessions
- **Working code at end of every session** — no "we'll fix it next time"
- **Failure modes demonstrated explicitly** — instructor breaks code on purpose to teach debugging patterns
- **Real APIs, real fanpages, real data** — no toy mocks; the project is more interesting because the stakes are real
