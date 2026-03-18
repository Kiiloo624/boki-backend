# Boki Backend — Architecture

## Overview

Boki's backend is split into two layers:

1. **Supabase** — managed Postgres database, auth, file storage, and realtime
2. **FastAPI** (this repo) — AI agent, scraper pipeline, Google Maps processing

The Flutter mobile app and any web clients talk **directly to Supabase** for all standard data operations (fetching venues, saving favorites, auth). They only call this FastAPI service for AI chatbot interactions and anything that requires server-side processing.

```
Flutter App / Web
       │
       ├──── Supabase (direct) ────► Postgres DB (venues, users, reviews, etc.)
       │                       ────► Auth (JWT)
       │                       ────► Storage (venue photos/videos)
       │
       └──── FastAPI (this repo) ──► AI Agent (Claude)
                                ──► Google Maps API
                                ──► Scraper (Scrapling)
```

## Why this split?

- Supabase SDKs exist for Flutter and TypeScript — no boilerplate for CRUD
- Agentic AI chains can run 10–30 seconds — not suitable for Edge Functions
- Python has the best AI tooling (Anthropic SDK, LangChain if needed)
- Scraping requires a real persistent server, not serverless

## Directory Structure

```
boki-backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── core/
│   │   ├── config.py            # All env vars via pydantic-settings
│   │   └── supabase.py          # Supabase client (service role)
│   ├── api/
│   │   └── routes/              # One file per feature area
│   │       ├── agent.py         # POST /agent/chat
│   │       ├── venues.py        # Venue-related endpoints
│   │       └── scraper.py       # Trigger/status for scrape jobs
│   ├── models/                  # SQLAlchemy or plain Pydantic DB models
│   ├── schemas/                 # Request/response Pydantic schemas
│   └── services/
│       ├── ai/                  # Agent logic, tool definitions, Claude calls
│       ├── scraper/             # Scrapling-based scrapers per source
│       └── maps/                # Google Maps API wrappers
├── scripts/                     # One-off admin scripts (seed data, etc.)
├── docs/                        # You are here
├── tests/
├── requirements.txt
├── .env.example
└── fly.toml                     # Fly.io deployment config
```
