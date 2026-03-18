# Boki Backend — Progress & Remaining Work

## What's Done

### Infrastructure
- FastAPI app scaffold (`app/main.py`, `app/core/config.py`, `app/core/supabase.py`)
- `.env` configured — Supabase, Gemini, SerpApi, Groq keys all set
- Supabase MCP connected (project ref: `tvlpcjmjdmrkmjdfgmza`)
- `.mcp.json` with Supabase personal access token
- **Deployed on Render**: https://boki-backend.onrender.com

### Database (Supabase)
- `venues` table — 26 columns covering all Phase 1 MVP fields
  - Location: address, city, district, lat/lng, landmark_directions
  - Pricing: min_spend, price_range (1–4 ₦ indicator)
  - Policies: camera_policy, age_restriction
  - Dropped: `entry_fee`, `dress_code` (not applicable to Nigerian venues)
  - Google data: google_place_id (unique), google_rating, google_reviews_count
  - Media: photos (JSONB array), opening_hours (JSONB)
  - Status: is_verified, is_active, scraped_at
- `venue_reviews` table — source (google/tripadvisor/curated), is_featured flag
- `venue_category` enum — bar, club, lounge, restaurant, rooftop, sports_bar,
  hookah_lounge, entertainment, cinema, park, amusement_park, casino, other
- `updated_at` trigger on venues
- RLS enabled on both tables:
  - `venues`: public SELECT on `is_active = true`
  - `venue_reviews`: public SELECT
- All migrations tracked via Supabase MCP

### Scraping Pipeline (`app/services/scraper/`)
- `serpapi.py` — SerpApi Google Maps client (search + place details)
- `transform.py` — raw result → DB row (slug gen, category mapping, district extraction)
- `pipeline.py` — **48 queries** covering all major Abuja districts and categories, dedupes on google_place_id
- `website_scraper.py` — Scrapling fetcher + Gemini extraction for pricing/policy from venue websites
- `enricher.py` — orchestrates website enrichment for venues missing key fields
- `price_inferencer.py` — Gemini batch inference of price_range (1–4) for all venues
- All scraper jobs run as **background tasks** — returns job_id immediately, poll `/scraper/status/{job_id}`

### Admin Routes (protected by `X-Admin-Key` header)
- `POST /scraper/run` — run full scrape (or custom queries)
- `POST /scraper/enrich` — enrich venues via website scraping + Gemini
- `POST /scraper/infer-prices` — infer price_range via Gemini for all venues
- `GET /scraper/status/{job_id}` — poll background job status

### Public API
- `GET /venues` — list with filters (category, district, price_range, search, is_verified), sort, pagination
- `GET /venues/nearby?lat&lng&radius_km&limit` — GPS proximity search, sorted by distance
- `GET /venues/{slug}` — full venue detail
- `GET /venues/districts` — districts with venue counts
- `GET /venues/categories` — categories with venue counts
- `GET /venues/{slug}/reviews` — paginated reviews (featured first)
- `POST /chat` — Boki AI assistant (Groq Llama 4 Scout, tool use)

### Admin Routes (protected by `X-Admin-Key` header)
- `POST /scraper/run` — run full scrape (or custom queries)
- `POST /scraper/enrich` — enrich venues via website scraping + Gemini
- `POST /scraper/infer-prices` — infer price_range via Gemini for all venues
- `POST /scraper/infer-landmarks` — infer landmark_directions via Gemini for all venues
- `GET /scraper/status/{job_id}` — poll background job status

### Pydantic Schemas
- `app/schemas/venue.py` — VenueSummary, VenueDetail, VenueNearby, DistrictCount, CategoryCount, VenueListResponse
- `app/schemas/review.py` — ReviewOut, ReviewListResponse

### Data
- **469 venues** in Supabase across Abuja
- All have: name, slug, category, district, lat/lng, google_rating, price_range
- **454/469 (97%)** have landmark_directions (Gemini-inferred)
- Price range distribution: ₦×29, ₦₦×70, ₦₦₦×76, ₦₦₦₦×5
- 24 venues have websites (scraping attempted)

---

## What's Left

### Phase 1 MVP — Complete ✅
All Phase 1 features are built and deployed. The API is live at https://boki-backend.onrender.com.

---

### Phase 2 — In Progress

#### 1. Chatbot (`POST /chat`) — DONE ✅
Files: `app/services/ai/chatbot.py`, `app/api/routes/chat.py`

Using Groq (`meta-llama/llama-4-scout-17b-16e-instruct`) with tool use for venue search.
- Switched from `llama-3.3-70b-versatile` → Llama 4 Scout to fix `tool_use_failed` errors
- ₦ symbols stripped from all tool descriptions
- `price_range` and `limit` declared as strings in schema (model returns strings; Python coerces to int)

Tools:
- `search_venues(category?, district?, price_range?, search?, limit?)` — queries Supabase
- `get_venue_detail(slug)` — full venue info

Request shape: `{ message: str, history: [{role, content}] }`
Response shape: `{ reply: str, venues: [...] }`

#### 2. User Authentication
- Supabase Auth (email/phone)
- Needed before: saved venues, user reviews, venue claiming

#### 3. Saved Venues
- Requires auth
- `saved_venues` table (user_id, venue_id)
- `POST /venues/{slug}/save`, `DELETE /venues/{slug}/save`, `GET /users/me/saved`

#### 4. User-submitted Reviews
- Requires auth
- `POST /venues/{slug}/reviews`

---

### Phase 3 — Scaling
- Trending leaderboard (views + saves + check-ins)
- Safety & utility ratings (community-sourced)
- Maps integration (lat/lng already in DB — waiting on budget)
- In-app bookings / table reservations
- Multi-city expansion (Lagos, Kano, Port Harcourt)
- Instagram scraping for high-quality photos

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/core/config.py` | All env vars (Supabase, Gemini, SerpApi, Groq) |
| `app/core/supabase.py` | Supabase service-role client |
| `app/core/gemini.py` | Single Gemini configure + model instance (shared by all scrapers) |
| `app/api/deps.py` | `require_admin_key` dependency |
| `app/services/scraper/pipeline.py` | Main scrape orchestrator (48 queries) |
| `app/services/scraper/price_inferencer.py` | Gemini price range inference |
| `app/services/scraper/landmark_inferencer.py` | Gemini landmark directions inference |
| `app/services/ai/chatbot.py` | Groq chatbot agent with tool use |
| `app/api/routes/scraper.py` | Admin scraper endpoints (background jobs) |
| `app/api/routes/venues.py` | Public venues endpoints (incl. /nearby) |
| `app/api/routes/reviews.py` | Public reviews endpoint |
| `app/api/routes/chat.py` | Chatbot endpoint |
| `app/main.py` | FastAPI app + route registration |
| `docs/progress.md` | This file |
| `docs/api.md` | Flutter integration reference |

## Models in Use
- **Gemini 2.5 Flash** — price inference, landmark inference, website data extraction (admin only)
- **Groq meta-llama/llama-4-scout-17b-16e-instruct** — chatbot (public-facing, free tier)
- **SerpApi** — Google Maps venue discovery (250 calls/month free; ~48 used per full scrape)
- **Scrapling AsyncFetcher** — website scraping (free, no limits)
