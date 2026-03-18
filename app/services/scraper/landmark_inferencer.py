import json
import logging
import re

from app.core.gemini import model
from app.core.supabase import supabase

logger = logging.getLogger(__name__)

BATCH_SIZE = 10

PROMPT = """You are an expert on Abuja, Nigeria. For each venue below, write a brief human-readable
direction that would help someone find it using local landmarks or street references.

Style: "Near [landmark], [area]" or "Opposite/Behind/Off [street], [district]"
Examples:
- "Opposite Transcorp Hilton, Maitama"
- "Off Aminu Kano Crescent, behind Sheraton Hotel, Wuse 2"
- "Inside Ceddi Plaza, Central Business District"
- "Along Airport Road, near Berger Junction, Lugbe"

Return ONLY a valid JSON object mapping each id to a direction string. If you genuinely cannot
infer a useful direction, use null for that id.

{{"id1": "...", "id2": null}}

Venues:
{venues}"""


def _format_venues(batch: list[dict]) -> str:
    lines = []
    for v in batch:
        lines.append(
            f"id={v['id']} | {v['name']} | address={v['address'] or 'N/A'} | district={v['district'] or 'unknown'}"
        )
    return "\n".join(lines)


def _parse_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def infer_landmark_directions(limit: int | None = None) -> dict:
    """
    Use Gemini to infer landmark_directions for all venues missing it.
    Processes venues in batches of 10.
    """
    query = (
        supabase.table("venues")
        .select("id, name, address, district")
        .is_("landmark_directions", "null")
    )
    if limit:
        query = query.limit(limit)

    venues = query.execute().data
    logger.info("Inferring landmark directions for %d venues", len(venues))

    updated = 0
    errors = 0

    for i in range(0, len(venues), BATCH_SIZE):
        batch = venues[i : i + BATCH_SIZE]
        prompt = PROMPT.format(venues=_format_venues(batch))

        try:
            response = model.generate_content(prompt)
            results = _parse_response(response.text)

            for venue_id, direction in results.items():
                if not direction:
                    continue
                supabase.table("venues").update({"landmark_directions": direction}).eq("id", venue_id).execute()
                updated += 1

            logger.info(
                "  Batch %d/%d — updated %d",
                i // BATCH_SIZE + 1,
                -(-len(venues) // BATCH_SIZE),
                sum(1 for v in results.values() if v),
            )

        except Exception as e:
            logger.error("  Batch %d failed: %s", i // BATCH_SIZE + 1, e)
            errors += 1

    logger.info("Landmark inference done — updated=%d errors=%d", updated, errors)
    return {"updated": updated, "errors": errors}
