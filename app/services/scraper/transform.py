import re
from datetime import datetime, timezone
from typing import Any

# Ordered longest-first so "Wuse 2" matches before "Wuse"
ABUJA_DISTRICTS = [
    "Wuse 2", "Wuse Zone 4", "Wuse Zone 5", "Wuse Zone 6", "Wuse",
    "Maitama", "Asokoro", "Garki", "Jabi", "Utako", "Gwarinpa",
    "Life Camp", "Lugbe", "Kubwa", "Kado", "Dawaki", "Durumi",
    "Central Business District", "CBD",
    "Area 1", "Area 2", "Area 3", "Area 11",
]


def extract_district(address: str | None) -> str | None:
    if not address:
        return None
    for district in ABUJA_DISTRICTS:
        if district.lower() in address.lower():
            # Normalise "CBD" to the full name
            return "Central Business District" if district == "CBD" else district
    return None


def generate_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug


def map_category(google_type: str | None) -> str:
    if not google_type:
        return "other"
    t = google_type.lower()
    if "amusement park" in t or "theme park" in t or "water park" in t:
        return "amusement_park"
    if "casino" in t:
        return "casino"
    if "cinema" in t or "movie theater" in t or "movie theatre" in t:
        return "cinema"
    if "park" in t or "garden" in t or "nature reserve" in t:
        return "park"
    if "bowling" in t or "arcade" in t or "entertainment center" in t or "entertainment complex" in t:
        return "entertainment"
    if "club" in t or "nightclub" in t:
        return "club"
    if "hookah" in t or "shisha" in t:
        return "hookah_lounge"
    if "lounge" in t:
        return "lounge"
    if "rooftop" in t:
        return "rooftop"
    if "sport" in t:
        return "sports_bar"
    if "bar" in t:
        return "bar"
    if "restaurant" in t or "food" in t or "eatery" in t:
        return "restaurant"
    return "other"


def serpapi_result_to_venue(result: dict[str, Any]) -> dict[str, Any]:
    """Transform a single SerpApi local_result into a venues table row."""
    name = result.get("title", "").strip()

    # Collect photos: thumbnail first, then any extras
    photos = []
    if result.get("thumbnail"):
        photos.append({"url": result["thumbnail"], "source": "google"})
    for p in result.get("photos", []):
        url = p.get("image") or p.get("thumbnail")
        if url and url not in {ph["url"] for ph in photos}:
            photos.append({"url": url, "source": "google"})

    gps = result.get("gps_coordinates", {})

    rating = result.get("rating")
    if rating is not None:
        try:
            rating = round(float(rating), 1)
        except (ValueError, TypeError):
            rating = None

    return {
        "name": name,
        "slug": generate_slug(name),
        "category": map_category(result.get("type")),
        "address": result.get("address"),
        "city": "Abuja",
        "district": extract_district(result.get("address")),
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude"),
        "phone": result.get("phone"),
        "website": result.get("website"),
        "google_place_id": result.get("place_id"),
        "google_rating": rating,
        "google_reviews_count": result.get("reviews"),
        "photos": photos,
        "opening_hours": result.get("hours"),
        "is_verified": False,
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
