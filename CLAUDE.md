# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server (auto-reload)
uvicorn app.main:app --reload

# Run tests
pytest

# Run a single test file
pytest tests/test_foo.py

# Deploy to Fly.io
fly deploy
```

Interactive API docs available at `http://localhost:8000/docs` when running locally.

## Architecture

Boki is a FastAPI backend for a Nigerian entertainment & nightlife discovery app (Abuja pilot). The app is read-only for Phase 1 — users browse venues, no auth required.

### Request flow
`Client → FastAPI (main.py) → Route → Service → Supabase`

### Key layers

**`app/core/`**
- `config.py` — single `Settings` object (pydantic-settings, reads from `.env`). Import as `from app.core.config import settings`.
- `supabase.py` — single service-role Supabase client. Always use this for DB operations (bypasses RLS). Import as `from app.core.supabase import supabase`.

**`app/api/routes/`**
Register routers in `app/main.py` with `app.include_router(router, prefix=..., tags=[...])`.

**`app/services/scraper/`** — data pipeline (admin-only, not called by end users):
- `pipeline.py` — discovers venues via SerpApi Google Maps (18 default Abuja queries), upserts to DB on `google_place_id`
- `transform.py` — maps raw SerpApi results to DB rows; contains `extract_district()` and `map_category()` logic
- `enricher.py` — fetches venue websites with Scrapling, extracts pricing/policy fields via Gemini
- `price_inferencer.py` — uses Gemini in batches of 20 to infer `price_range` (1–4) for all venues
- `serpapi.py` — thin async httpx wrapper around SerpApi REST API
- `website_scraper.py` — Scrapling `AsyncFetcher` + Gemini extraction; skips Instagram/social URLs automatically

**`app/services/ai/`** — scaffolded for Phase 2 Gemini agent (not yet built)

**`app/schemas/`**, **`app/models/`** — currently empty stubs, to be populated as API routes are built

### Database (Supabase)
Two tables: `venues` and `venue_reviews`. Key design decisions:
- `google_place_id` is the deduplication key for scraping upserts
- `slug` is unique — used as the public identifier in API URLs
- `price_range` (1–4 ₦ indicator) is Gemini-inferred, not scraped
- `photos` and `opening_hours` are JSONB columns
- `district` is extracted from the address string via keyword matching (see `ABUJA_DISTRICTS` list in `transform.py`)
- RLS is **not yet enabled** — must be added before production

The Supabase MCP is configured in `.mcp.json` — use it for schema changes (`apply_migration`) and queries (`execute_sql`) instead of writing migration files manually.

### Gemini usage
Both `website_scraper.py` and `price_inferencer.py` call `genai.configure()` at module import time. The model is `gemini-2.5-flash`. Do not add a third configure call elsewhere — consolidate into `app/core/` if more AI services are added.

### Admin routes
`POST /scraper/run`, `/scraper/enrich`, `/scraper/infer-prices` have no auth protection yet. Before production, add an `X-Admin-Key` header check using an `ADMIN_API_KEY` env var.

### What's built vs. what's next
See `docs/progress.md` for the full breakdown. Short version: scraping pipeline is complete (217 Abuja venues in DB). Still needed for Phase 1 MVP: Venues API (`GET /venues`, `GET /venues/{slug}`), Reviews API, RLS, admin route protection, and Fly.io deployment.
