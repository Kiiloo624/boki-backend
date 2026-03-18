import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings
from app.core.supabase import supabase

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.5-flash")

BATCH_SIZE = 20

PROMPT = """You are an expert on Abuja, Nigeria's entertainment and nightlife scene.

For each venue, estimate its price range on a 1-4 scale based on typical spend per person:
1 = Budget (₦)        — under ₦5,000   e.g. local bars, public parks, regular cinemas
2 = Mid-range (₦₦)    — ₦5,000–15,000  e.g. popular restaurants, lounges, bowling
3 = Upscale (₦₦₦)     — ₦15,000–50,000 e.g. premium clubs, rooftop bars, hotel lounges
4 = Luxury (₦₦₦₦)     — ₦50,000+       e.g. Maitama/Asokoro elite clubs, high-end casinos

Key signals:
- Districts: Asokoro/Maitama lean 3-4 | Wuse 2/Garki lean 2-3 | Gwarinpa/outskirts lean 1-2
- Categories: casino=3-4 | club/rooftop=2-4 | lounge/bar=2-3 | restaurant=1-3 | park/cinema=1-2
- Name keywords: "elite", "premium", "royal", "grand", "luxury" → higher range
- High Google rating (4.6+) in Abuja often signals upscale

Return ONLY a valid JSON object mapping each id to a price_range integer, nothing else:
{{"id1": 2, "id2": 3}}

Venues:
{venues}"""


def _format_venues(batch: list[dict]) -> str:
    lines = []
    for v in batch:
        lines.append(
            f"id={v['id']} | {v['name']} | district={v['district'] or 'unknown'} "
            f"| category={v['category']} | rating={v['google_rating'] or 'N/A'}"
        )
    return "\n".join(lines)


def _parse_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def infer_price_ranges(limit: int | None = None) -> dict:
    """
    Use Gemini to infer price_range (1-4) for all venues missing it.
    Processes venues in batches of 20 to minimise API calls.
    """
    query = (
        supabase.table("venues")
        .select("id, name, district, category, google_rating")
        .is_("price_range", "null")
    )
    if limit:
        query = query.limit(limit)

    venues = query.execute().data
    logger.info("Inferring price range for %d venues", len(venues))

    updated = 0
    errors = 0

    for i in range(0, len(venues), BATCH_SIZE):
        batch = venues[i : i + BATCH_SIZE]
        prompt = PROMPT.format(venues=_format_venues(batch))

        try:
            response = _model.generate_content(prompt)
            results = _parse_response(response.text)

            for venue_id, price_range in results.items():
                if price_range not in (1, 2, 3, 4):
                    continue
                supabase.table("venues").update({"price_range": price_range}).eq("id", venue_id).execute()
                updated += 1

            logger.info("  Batch %d/%d — updated %d", i // BATCH_SIZE + 1, -(-len(venues) // BATCH_SIZE), len(results))

        except Exception as e:
            logger.error("  Batch %d failed: %s", i // BATCH_SIZE + 1, e)
            errors += 1

    logger.info("Price inference done — updated=%d errors=%d", updated, errors)
    return {"updated": updated, "errors": errors}
