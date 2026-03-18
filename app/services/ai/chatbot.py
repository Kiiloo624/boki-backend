import json
from groq import AsyncGroq
from app.core.config import settings
from app.core.supabase import supabase

client = AsyncGroq(api_key=settings.GROQ_API_KEY)
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """You are Boki, an AI assistant for a Nigerian nightlife and entertainment discovery app in Abuja.
Help users find venues, answer questions about places, and give personalised recommendations.
Be concise and friendly. Always use your tools to fetch real data — never make up venue details.
Price ranges: 1=budget, 2=mid-range, 3=upscale, 4=luxury."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_venues",
            "description": "Search for venues in Abuja with optional filters. Use this to find bars, clubs, restaurants, lounges, parks, and more.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["bar", "club", "lounge", "restaurant", "rooftop", "sports_bar",
                                 "hookah_lounge", "entertainment", "cinema", "park",
                                 "amusement_park", "casino", "other"],
                        "description": "Type of venue",
                    },
                    "district": {
                        "type": "string",
                        "description": "Abuja district e.g. Maitama, Wuse 2, Garki, Jabi, Asokoro, Utako",
                    },
                    "price_range": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4"],
                        "description": "1=budget, 2=mid-range, 3=upscale, 4=luxury",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search by venue name",
                    },
                    "limit": {
                        "type": "string",
                        "description": "Max results to return, default 5, max 10",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_venue_detail",
            "description": "Get full details for a specific venue: pricing, dress code, opening hours, directions, phone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The venue's slug identifier",
                    }
                },
                "required": ["slug"],
            },
        },
    },
]


def _search_venues(category=None, district=None, price_range=None, search=None, limit=5):
    limit = min(int(limit) if limit else 5, 10)
    if price_range is not None:
        price_range = int(price_range)
    query = (
        supabase.table("venues")
        .select("name, slug, category, district, price_range, google_rating, google_reviews_count, photos, min_spend, opening_hours, phone")
        .eq("is_active", True)
    )
    if category:
        query = query.eq("category", category)
    if district:
        query = query.eq("district", district)
    if price_range:
        query = query.eq("price_range", price_range)
    if search:
        query = query.ilike("name", f"%{search}%")
    return query.order("google_rating", desc=True).limit(limit).execute().data


def _get_venue_detail(slug: str):
    return (
        supabase.table("venues")
        .select("*")
        .eq("slug", slug)
        .eq("is_active", True)
        .maybe_single()
        .execute()
        .data
    )


def _execute_tool(name: str, args: dict):
    if name == "search_venues":
        return _search_venues(**args)
    if name == "get_venue_detail":
        return _get_venue_detail(**args)
    return {"error": "Unknown tool"}


async def chat(message: str, history: list[dict]) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    fetched_venues = []

    for _ in range(3):  # max 3 tool-call rounds
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        msg = response.choices[0].message

        # Append assistant turn as a plain dict for the next round
        assistant_turn = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_turn["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_turn)

        if not msg.tool_calls:
            return {"reply": msg.content, "venues": fetched_venues}

        # Execute tools and feed results back
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = _execute_tool(tc.function.name, args)

            if tc.function.name == "search_venues" and isinstance(result, list):
                fetched_venues.extend(result)
            elif tc.function.name == "get_venue_detail" and result:
                fetched_venues.append(result)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    # Shouldn't reach here, but get a final reply if we do
    final = await client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=1024
    )
    return {"reply": final.choices[0].message.content, "venues": fetched_venues}
