# External Services Setup

## 1. Google Gemini API

Used for: the AI agent / chatbot

Since you're already on Google Cloud for Maps, use the same account:

1. Go to https://aistudio.google.com
2. Sign in with your Google account
3. Click **Get API Key** → **Create API key in new project** (or select your existing "boki" project)
4. Copy the key into `.env` as `GEMINI_API_KEY`

**Model to use:** `gemini-2.0-flash` — fast, capable, excellent at tool use / function calling

**Cost:**
- **Free tier:** 1,500 requests/day, 1M tokens/minute — covers MVP entirely
- **Paid:** $0.10 per 1M input tokens (vs Claude's $3/1M — 30x cheaper)
- One Google Cloud account covers both Gemini and Maps billing

**Note:** The free tier has no time limit — it's not a trial credit, it's the permanent free quota.

---

## 2. Google Maps Platform

Used for: venue geocoding, directions, nearby search, place details

### Setup Steps

1. Go to https://console.cloud.google.com
2. Create a new project called "boki"
3. Go to **APIs & Services → Library** and enable:
   - **Maps JavaScript API** (if you add a web map view)
   - **Places API** (search venues, get details)
   - **Geocoding API** (convert addresses to lat/lng)
   - **Directions API** (landmark-based directions)
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. **Restrict the key** (important):
   - Application restrictions: IP addresses (add your Fly.io server IP later)
   - API restrictions: select only the 4 APIs above
6. Copy into `.env` as `GOOGLE_MAPS_API_KEY`

**Estimated cost:**
- Geocoding: $5 per 1,000 requests (free tier: $200/month credit)
- Places: $17–$32 per 1,000 requests
- $200/month free credit covers ~6,000–10,000 requests — more than enough for MVP

**Important:** Google Maps free credit resets monthly. You won't pay anything during MVP if traffic is low.

---

## 3. Scrapling

Used for: scraping venue data from Nigerian listing sites and social media

No API key needed — it's a Python library. Install via requirements.txt.

### Sources to target (suggested priority):
1. Google Maps (search "bars in Wuse 2 Abuja") — use Places API instead of scraping
2. Nairaland venue listings
3. Venue Instagram profiles (for photos and opening hours)
4. Individual venue websites

### Basic usage:
```python
from scrapling import StealthyFetcher

fetcher = StealthyFetcher()
page = fetcher.fetch("https://target-site.com/venues")
venues = page.css(".venue-card")
```

See `app/services/scraper/` for full scrapers once built.

---

## 4. Fly.io (Hosting)

Used for: hosting the FastAPI service

### Free Tier Includes:
- 3 shared-CPU VMs (256MB RAM each)
- 3GB persistent storage
- Enough for MVP — FastAPI + scraper fits in 256MB easily

### Setup Steps

1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
2. Sign up: `fly auth signup`
3. From the repo root: `fly launch`
   - App name: `boki-api`
   - Region: `lhr` (London — closest to Nigeria)
   - Don't deploy yet
4. Set your secrets (env vars):
```bash
fly secrets set SUPABASE_URL=your-url
fly secrets set SUPABASE_SERVICE_ROLE_KEY=your-key
fly secrets set GEMINI_API_KEY=your-key
fly secrets set GOOGLE_MAPS_API_KEY=your-key
```
5. Deploy: `fly deploy`

Your API will be at: `https://boki-api.fly.dev`

### fly.toml (already in repo root — edit app name if needed)

---

## 5. Summary Table

| Service | Free Tier | Paid starts at | Sign up URL |
|---|---|---|---|
| Supabase | 500MB DB, 1GB storage, 50k MAU | $25/mo | supabase.com |
| Gemini API | 1,500 req/day free (permanent) | $0.10/1M tokens | aistudio.google.com |
| Google Maps | $200/mo credit | Pay as you go | console.cloud.google.com |
| Fly.io | 3 VMs always free | $5/mo | fly.io |
| GitHub | Unlimited public repos | Free | github.com |

**Total cost to start: $0**
