import httpx
from app.core.config import settings

SERPAPI_BASE = "https://serpapi.com/search.json"


async def search_google_maps(query: str, gps: str | None = None) -> dict:
    """
    Search Google Maps via SerpApi.
    gps: "@lat,lng,zoom" e.g. "@9.0579,7.4951,14z"
    """
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": settings.SERPAPI_KEY,
    }
    if gps:
        params["ll"] = gps

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(SERPAPI_BASE, params=params)
        r.raise_for_status()
        return r.json()


async def get_place_details(place_id: str) -> dict:
    """Fetch full details for a single place by Google place_id."""
    params = {
        "engine": "google_maps",
        "place_id": place_id,
        "type": "place",
        "api_key": settings.SERPAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(SERPAPI_BASE, params=params)
        r.raise_for_status()
        return r.json()
