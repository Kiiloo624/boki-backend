# Boki Backend — Progress & Remaining Work

## What's Done

### Infrastructure
- FastAPI app scaffold (`app/main.py`, `app/core/config.py`, `app/core/supabase.py`)
- `.env` configured — Supabase, Gemini, SerpApi keys all set
- Supabase MCP connected (project ref: `tvlpcjmjdmrkmjdfgmza`)
- `.mcp.json` with Supabase personal access token

### Database (Supabase)
- `venues` table — 28 columns covering all Phase 1 MVP fields
  - Location: address, city, district, lat/lng, landmark_directions
  - Pricing: entry_fee, min_spend, price_range (1–4 ₦ indicator)
  - Policies: dress_code, camera_policy, age_restriction
  - Google data: google_place_id (unique), google_rating, google_reviews_count
  - Media: photos (JSONB array), opening_hours (JSONB)
  - Status: is_verified, is_active, scraped_at
- `venue_reviews` table — source (google/tripadvisor/curated), is_featured flag
- `venue_category` enum — bar, club, lounge, restaurant, rooftop, sports_bar,
  hookah_lounge, entertainment, cinema, park, amusement_park, casino, other
- `updated_at` trigger on venues
- All migrations tracked via Supabase MCP

### Scraping Pipeline (`app/services/scraper/`)
- `serpapi.py` — SerpApi Google Maps client (search + place details)
- `transform.py` — raw result → DB row (slug gen, category mapping, district extraction)
- `pipeline.py` — 18 default queries, dedupes on google_place_id, skips social URLs
- `website_scraper.py` — Scrapling fetcher + Gemini extraction for pricing/policy from venue websites
- `enricher.py` — orchestrates website enrichment for venues missing key fields
- `price_inferencer.py` — Gemini batch inference of price_range (1–4) for all venues

### Admin Routes (`POST`, no auth yet)
- `POST /scraper/run` — run full scrape (or custom queries)
- `POST /scraper/enrich` — enrich venues via website scraping + Gemini
- `POST /scraper/infer-prices` — infer price_range via Gemini for all venues

### Data
- **217 venues** in Supabase across Abuja
- All have: name, slug, category, district, lat/lng, google_rating, price_range
- 24 venues have websites (scraping attempted; most Nigerian venues don't publish policies online)
- Price range distribution: ₦×29, ₦₦×70, ₦₦₦×76, ₦₦₦₦×5

---

## What's Left

### Phase 1 MVP — Must Build Next

#### 1. Venues API (`app/api/routes/venues.py`)
The core public-facing API. Suggested endpoints:
```
GET  /venues              — list with filters
GET  /venues/{slug}       — single venue detail
GET  /venues/districts    — list of districts with venue counts
GET  /venues/categories   — list of categories with venue counts
```
Filter params for list: `category`, `district`, `price_range`, `search` (name), `is_verified`
Sorting: `google_rating`, `google_reviews_count`, `name`
Pagination: `limit` + `offset`

Pydantic response schemas needed in `app/schemas/venue.py`:
- `VenueSummary` — for list view (id, name, slug, category, district, price_range, google_rating, photos[0])
- `VenueDetail` — full venue + reviews

#### 2. Reviews API (`app/api/routes/reviews.py`)
```
GET /venues/{slug}/reviews   — paginated reviews for a venue
```
Response schema in `app/schemas/review.py`

#### 3. Pydantic Schemas (`app/schemas/`)
- `venue.py` — VenueSummary, VenueDetail, VenueListResponse
- `review.py` — ReviewOut, ReviewListResponse

#### 4. Supabase Row Level Security (RLS)
Currently RLS is disabled on both tables. Before going to production:
- Enable RLS on `venues` — allow public `SELECT` on `is_active = true`
- Enable RLS on `venue_reviews` — allow public `SELECT`
- Service role key (used by backend) bypasses RLS automatically

Apply via Supabase MCP:
```sql
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public can read active venues"
  ON venues FOR SELECT USING (is_active = true);

ALTER TABLE venue_reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public can read reviews"
  ON venue_reviews FOR SELECT USING (true);
```

#### 5. Protect Admin Routes
The scraper routes (`/scraper/*`) have no auth. Add a simple API key check before deploying:
- Add `ADMIN_API_KEY` to `.env` and `config.py`
- Add a FastAPI dependency that checks `X-Admin-Key` header

#### 6. Dockerfile & Fly.io Deployment
`Dockerfile` and `fly.toml` already exist in the repo — review and deploy.

---

### Phase 2 — Growth Features (after MVP launch)
- User authentication (Supabase Auth — email/phone)
- User-submitted reviews + photos
- Venue claiming by owners
- WhatsApp integration (direct button)
- Social sharing cards
- Push notifications (new venues, price changes)

### Phase 3 — Scaling
- Trending leaderboard (views + saves + check-ins)
- Safety & utility ratings (community-sourced)
- AI recommendations (Gemini agent — already scaffolded in `app/services/ai/`)
- In-app bookings / table reservations
- Multi-city expansion (Lagos, Kano, Port Harcourt)
- Instagram scraping for high-quality photos (Scrapling + Playwright)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/core/config.py` | All env vars (Supabase, Gemini, SerpApi) |
| `app/core/supabase.py` | Supabase service-role client |
| `app/services/scraper/pipeline.py` | Main scrape orchestrator |
| `app/services/scraper/price_inferencer.py` | Gemini price range inference |
| `app/api/routes/scraper.py` | Admin scraper endpoints |
| `app/main.py` | FastAPI app + route registration |
| `.mcp.json` | Supabase MCP config |
| `docs/progress.md` | This file |

## Models in Use
- **Gemini 2.5 Flash** — price inference + website data extraction
- **SerpApi** — Google Maps venue discovery (250 calls/month free; ~18 used per full scrape)
- **Scrapling AsyncFetcher** — website scraping (free, no limits)
