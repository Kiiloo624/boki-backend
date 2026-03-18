import logging
from app.services.scraper.serpapi import search_google_maps
from app.services.scraper.transform import serpapi_result_to_venue
from app.core.supabase import supabase

logger = logging.getLogger(__name__)

# Abuja city centre GPS for proximity-biased results
ABUJA_GPS = "@9.0579,7.4951,14z"

DEFAULT_QUERIES = [
    # --- Bars by district ---
    "bars in Wuse 2 Abuja",
    "bars in Maitama Abuja",
    "bars in Garki Abuja",
    "bars in Jabi Abuja",
    "bars in Utako Abuja",
    "bars in Asokoro Abuja",
    "bars in Central Business District Abuja",
    "bars in Life Camp Abuja",
    "bars in Gwarinpa Abuja",
    "pubs in Abuja",
    "wine bar Abuja",
    "cocktail bar Abuja",

    # --- Clubs & lounges ---
    "nightclubs in Abuja",
    "nightclub Wuse 2 Abuja",
    "nightclub Maitama Abuja",
    "nightclub Jabi Abuja",
    "lounges in Abuja",
    "lounge Jabi Abuja",
    "lounge Asokoro Abuja",
    "lounge Wuse 2 Abuja",

    # --- Specialty nightlife ---
    "rooftop bars Abuja",
    "rooftop restaurant Abuja",
    "sports bar Abuja",
    "hookah lounge Abuja",
    "shisha lounge Abuja",
    "live music venue Abuja",
    "karaoke bar Abuja",

    # --- Restaurants by district ---
    "restaurants in Wuse 2 Abuja",
    "restaurants in Maitama Abuja",
    "restaurants in Garki Abuja",
    "restaurants in Jabi Abuja",
    "restaurants in Utako Abuja",
    "restaurants in Asokoro Abuja",
    "restaurants in Central Business District Abuja",
    "restaurants in Life Camp Abuja",
    "restaurants in Gwarinpa Abuja",

    # --- Entertainment & leisure ---
    "entertainment centers in Abuja",
    "bowling alley Abuja",
    "amusement park Abuja",
    "cinemas in Abuja",
    "parks in Abuja",
    "casinos in Abuja",
    "resort Abuja",
    "swimming pool club Abuja",
    "arcade game center Abuja",
    "go kart Abuja",
    "trampoline park Abuja",
    "escape room Abuja",
]


async def scrape_and_save(queries: list[str] = DEFAULT_QUERIES) -> dict:
    """
    Run each query against SerpApi Google Maps, transform results,
    and upsert into the venues table (deduplicates on google_place_id).
    """
    saved = 0
    skipped = 0
    errors = 0
    # Track place_ids seen this run to skip exact duplicates across queries
    seen_place_ids: set[str] = set()

    for query in queries:
        logger.info("Scraping: %s", query)
        try:
            data = await search_google_maps(query, gps=ABUJA_GPS)
            results = data.get("local_results", [])
            logger.info("  → %d results", len(results))

            for result in results:
                try:
                    venue = serpapi_result_to_venue(result)

                    place_id = venue.get("google_place_id")
                    if not place_id:
                        logger.debug("  Skipping '%s' — no place_id", venue.get("name"))
                        skipped += 1
                        continue

                    # Skip if already processed in this run
                    if place_id in seen_place_ids:
                        skipped += 1
                        continue
                    seen_place_ids.add(place_id)

                    # Ensure slug is unique: append place_id suffix on collision
                    base_slug = venue["slug"]
                    existing = (
                        supabase.table("venues")
                        .select("id")
                        .eq("slug", base_slug)
                        .neq("google_place_id", place_id)
                        .execute()
                    )
                    if existing.data:
                        venue["slug"] = f"{base_slug}-{place_id[-6:].lower()}"

                    # Remove null district so existing value isn't overwritten
                    if venue.get("district") is None:
                        venue.pop("district", None)

                    supabase.table("venues").upsert(
                        venue, on_conflict="google_place_id"
                    ).execute()
                    saved += 1
                    logger.debug("  Saved: %s", venue["name"])

                except Exception as e:
                    logger.error("  Error saving '%s': %s", result.get("title"), e)
                    errors += 1

        except Exception as e:
            logger.error("Error scraping '%s': %s", query, e)
            errors += 1

    logger.info("Done — saved=%d skipped=%d errors=%d", saved, skipped, errors)
    return {"saved": saved, "skipped": skipped, "errors": errors}
