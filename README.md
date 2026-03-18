# Boki Backend

FastAPI service for the Boki nightlife discovery app. Handles the AI agent, Google Maps integration, and venue data scraping.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # Fill in your keys
uvicorn app.main:app --reload
```

Docs at http://localhost:8000/docs

## Documentation

| Doc | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | How everything fits together |
| [Supabase Setup](docs/SUPABASE_SETUP.md) | DB schema, RLS, storage buckets, Flutter SDK |
| [FastAPI Setup](docs/FASTAPI_SETUP.md) | Local dev, project structure, adding routes |
| [Services Setup](docs/SERVICES_SETUP.md) | Anthropic, Google Maps, Scrapling, Fly.io |
| [AI Agent Design](docs/AI_AGENT.md) | How the chatbot works, tool use, rate limiting |

## Stack

- **FastAPI** — API framework
- **Supabase** — Postgres database, auth, storage
- **Claude (claude-sonnet-4-6)** — AI agent
- **Scrapling** — Anti-bot web scraping
- **Google Maps Platform** — Geocoding, Places, Directions
- **Fly.io** — Hosting (free tier)
