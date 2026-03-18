import logging
from app.services.scraper.website_scraper import fetch_website_text, extract_venue_fields, is_social_url
from app.core.supabase import supabase

logger = logging.getLogger(__name__)

# Fields we consider "missing" — if all are null, venue needs enrichment
ENRICHABLE_FIELDS = ["min_spend", "camera_policy", "whatsapp"]


async def enrich_venues(limit: int = 20) -> dict:
    """
    Enrich venues that have a website URL but are missing key policy/pricing fields.
    Fetches each website with Scrapling, sends text to Gemini, updates the DB.
    """
    # Find venues with a website but no pricing/policy data yet
    response = (
        supabase.table("venues")
        .select("id, name, website")
        .not_.is_("website", "null")
        .is_("min_spend", "null")
        .limit(limit)
        .execute()
    )

    venues = response.data
    logger.info("Enriching %d venues", len(venues))

    enriched = 0
    no_data = 0
    failed = 0
    skipped = 0

    for venue in venues:
        url = venue["website"]
        name = venue["name"]

        if is_social_url(url):
            logger.debug("  Skipping social URL for %s", name)
            skipped += 1
            continue

        logger.info("  Enriching: %s (%s)", name, url)

        text = await fetch_website_text(url)
        if not text:
            logger.debug("  No text fetched for %s", name)
            failed += 1
            continue

        fields = await extract_venue_fields(text, name)

        if not fields:
            logger.debug("  No fields extracted for %s", name)
            no_data += 1
            continue

        supabase.table("venues").update(fields).eq("id", venue["id"]).execute()
        logger.info("  Updated %s: %s", name, list(fields.keys()))
        enriched += 1

    logger.info("Enrichment done — enriched=%d no_data=%d failed=%d skipped=%d", enriched, no_data, failed, skipped)
    return {"enriched": enriched, "no_data": no_data, "failed": failed, "skipped_social": skipped}
