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
- `gemini.py` — single Gemini configure + model instance. Import as `from app.core.gemini import model`. Do NOT call `genai.configure()` anywhere else.

**`app/api/routes/`**
Register routers in `app/main.py` with `app.include_router(router, prefix=..., tags=[...])`.

**`app/services/scraper/`** — data pipeline (admin-only, not called by end users):
- `pipeline.py` — discovers venues via SerpApi Google Maps (48 default Abuja queries), upserts to DB on `google_place_id`
- `transform.py` — maps raw SerpApi results to DB rows; contains `extract_district()` and `map_category()` logic
- `enricher.py` — fetches venue websites with Scrapling, extracts pricing/policy fields via Gemini
- `price_inferencer.py` — uses Gemini in batches of 20 to infer `price_range` (1–4) for all venues
- `landmark_inferencer.py` — uses Gemini in batches of 10 to infer `landmark_directions` for all venues
- `serpapi.py` — thin async httpx wrapper around SerpApi REST API
- `website_scraper.py` — Scrapling `AsyncFetcher` + Gemini extraction; skips Instagram/social URLs automatically

**`app/services/ai/`**
- `chatbot.py` — Groq Llama 4 Scout chatbot with tool use (`search_venues`, `get_venue_detail`)

**`app/schemas/`**
- `venue.py` — VenueSummary, VenueDetail, VenueNearby, DistrictCount, CategoryCount, VenueListResponse
- `review.py` — ReviewOut, ReviewListResponse

### Database (Supabase)
Two tables: `venues` and `venue_reviews`. Key design decisions:
- `google_place_id` is the deduplication key for scraping upserts
- `slug` is unique — used as the public identifier in API URLs
- `price_range` (1–4 ₦ indicator) is Gemini-inferred, not scraped
- `landmark_directions` is Gemini-inferred from venue name + address (97% coverage)
- `photos` and `opening_hours` are JSONB columns
- `entry_fee` and `dress_code` were dropped — not applicable to Nigerian venues
- `district` is extracted from the address string via keyword matching (see `ABUJA_DISTRICTS` list in `transform.py`)
- `cube` and `earthdistance` extensions enabled; `nearby_venues(user_lat, user_lng, radius_km, result_limit)` RPC function handles GPS proximity search
- RLS is enabled on both tables

The Supabase MCP is configured in `.mcp.json` — use it for schema changes (`apply_migration`) and queries (`execute_sql`) instead of writing migration files manually.

### Admin routes
All admin routes are protected by `X-Admin-Key` header (checked via `require_admin_key` dependency in `app/api/deps.py`):
- `POST /scraper/run` — full scrape
- `POST /scraper/enrich` — website enrichment
- `POST /scraper/infer-prices` — Gemini price inference
- `POST /scraper/infer-landmarks` — Gemini landmark inference
- `GET /scraper/status/{job_id}` — poll background job

### What's built vs. what's next
See `docs/progress.md` for full status and `docs/api.md` for the Flutter integration reference.
**Phase 1 complete. Phase 2 chatbot complete. Next: Supabase Auth → saved venues → user reviews.**
