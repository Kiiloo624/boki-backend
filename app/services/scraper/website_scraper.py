import json
import logging
import re
from urllib.parse import urljoin, urlparse

from scrapling.fetchers import AsyncFetcher

from app.core.gemini import model as _model

logger = logging.getLogger(__name__)

# Social/app URLs that will never contain venue policy text
SKIP_DOMAINS = {
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "tiktok.com", "youtube.com", "linktr.ee", "linkree.com",
}

# Sub-pages likely to contain pricing/policy info
ENRICHMENT_PATHS = ["/menu", "/about", "/contact", "/info", "/faq", "/book", "/reservations"]

EXTRACTION_PROMPT = """You are extracting nightlife venue information from a website.
Venue name: {name}

Return ONLY a valid JSON object with these fields (use null if not found on the page):
{{
  "min_spend": "e.g. N10,000 per table, or null",
  "camera_policy": "e.g. No professional cameras, or null",
  "whatsapp": "phone number used for WhatsApp, or null",
  "landmark_directions": "human-readable directions e.g. Opposite First Bank on Ademola Adetokunbo, or null"
}}

Website text:
{text}"""


def is_social_url(url: str) -> bool:
    domain = urlparse(url).netloc.lstrip("www.")
    return any(skip in domain for skip in SKIP_DOMAINS)


async def _fetch_text(url: str) -> str | None:
    try:
        page = await AsyncFetcher(auto_match=False).get(url, timeout=15)
        return str(page.get_all_text(separator=" ", strip=True))
    except Exception as e:
        logger.debug("Could not fetch %s: %s", url, e)
        return None


async def fetch_website_text(url: str) -> str | None:
    """Fetch venue website text, trying sub-pages if the homepage is thin."""
    if is_social_url(url):
        logger.debug("Skipping social URL: %s", url)
        return None

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    texts = []

    # Always fetch the homepage
    home_text = await _fetch_text(url)
    if home_text:
        texts.append(home_text)

    # Try enrichment sub-pages to find pricing/policy info
    for path in ENRICHMENT_PATHS:
        sub_text = await _fetch_text(urljoin(base, path))
        if sub_text:
            texts.append(sub_text)

    return " ".join(texts) if texts else None


async def extract_venue_fields(text: str, venue_name: str) -> dict:
    # Trim to avoid burning tokens on boilerplate
    truncated = text[:4000]
    prompt = EXTRACTION_PROMPT.format(name=venue_name, text=truncated)

    try:
        response = _model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        # Return only non-null values
        return {k: v for k, v in data.items() if v is not None}
    except Exception as e:
        logger.debug("Gemini extraction failed for '%s': %s", venue_name, e)
        return {}
