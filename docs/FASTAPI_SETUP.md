# FastAPI Setup Guide

## 1. Prerequisites

- Python 3.11+ installed
- pip or uv (uv is faster — recommended)

Install uv if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Local Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/your-org/boki-backend.git
cd boki-backend

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Now edit .env with your actual keys (see docs/SUPABASE_SETUP.md and docs/SERVICES_SETUP.md)

# Run the dev server
uvicorn app.main:app --reload --port 8000
```

API will be live at http://localhost:8000
Interactive docs at http://localhost:8000/docs

## 3. Project Structure Explained

### `app/core/config.py`
All configuration lives here via `pydantic-settings`. It reads from `.env` automatically.
To add a new env var: add a field to the `Settings` class, then add it to `.env.example`.

### `app/core/supabase.py`
Single Supabase client instance using the service role key. Import it anywhere:
```python
from app.core.supabase import supabase

result = supabase.table("venues").select("*").execute()
```

### `app/api/routes/`
Each file is a FastAPI router. Register new routers in `app/main.py`:
```python
from app.api.routes import agent
app.include_router(agent.router, prefix="/agent", tags=["agent"])
```

### `app/services/`
Business logic — keep routes thin, services fat.
- `ai/` — Claude agent, tool definitions, action rate limiting
- `scraper/` — Scrapling scrapers, one file per data source
- `maps/` — Google Maps API wrappers (geocoding, places, directions)

## 4. Adding a New Route (Example)

```python
# app/api/routes/venues.py
from fastapi import APIRouter
from app.core.supabase import supabase

router = APIRouter()

@router.get("/")
async def list_venues(city: str = "Abuja", district: str = None):
    query = supabase.table("venues").select("*").eq("city", city)
    if district:
        query = query.eq("district", district)
    result = query.execute()
    return result.data
```

## 5. Running Tests

```bash
pytest tests/ -v
```

## 6. Environment Variables Reference

See `.env.example` for the full list. Key ones:

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Full DB access — backend only |
| `SUPABASE_ANON_KEY` | Yes | For verifying user tokens |
| `ANTHROPIC_API_KEY` | Yes | Claude API for the AI agent |
| `GOOGLE_MAPS_API_KEY` | Yes | Maps, Places, Geocoding, Directions |
| `AGENT_DAILY_ACTION_LIMIT` | No | Default: 10 actions per user per day |
