# AI Agent Design

## Overview

The Boki chatbot is an AI agent powered by Gemini 2.0 Flash. It can understand natural language from the user and perform actions within the app — not just answer questions.

Example interactions:
- *"Find me a lounge in Maitama with a rooftop"* → searches venues
- *"Save Zinc to my favorites"* → writes to Supabase
- *"How do I get to Status Lounge from Wuse 2?"* → calls Google Maps Directions API
- *"What's the entry fee at Cube?"* → queries venue data

## Architecture: Tool Use (Function Calling)

Gemini supports "function calling" — you define a set of functions, and Gemini decides which ones to call based on the user's message. Your FastAPI service executes the actual function and returns the result to Gemini, which then responds naturally.

```
User message
    │
    ▼
FastAPI /agent/chat
    │
    ▼
Gemini 2.0 Flash (gemini-2.0-flash)
    │  ← tool definitions sent with every request
    │
    ├── calls tool: search_venues(district="Maitama", type="lounge")
    │       │
    │       └──► Supabase query → returns venue list
    │
    ├── calls tool: save_favorite(venue_id="abc123", user_id="xyz")
    │       │
    │       └──► Supabase insert → confirms save
    │
    └── Final response text to user
```

## Rate Limiting

Free app — limit agent actions to prevent abuse:
- Max **10 actions per device per 24 hours** (configurable via `AGENT_DAILY_ACTION_LIMIT`)
- Logged in `agent_action_log` table in Supabase
- Anonymous users identified by `device_id` (Flutter generates a UUID on first install)
- Authenticated users identified by `user_id`

## Tool Definitions (to build)

These are the tools Gemini will have access to:

| Tool name | Description | Phase |
|---|---|---|
| `search_venues` | Search by city, district, category, keywords | 1 |
| `get_venue_details` | Get full info for a specific venue | 1 |
| `get_directions` | Get landmark-based directions via Google Maps | 1 |
| `save_favorite` | Save a venue to user's bookmarks | 1 |
| `remove_favorite` | Remove from bookmarks | 1 |
| `list_favorites` | List user's saved venues | 2 |
| `post_review` | Post a review for a venue | 2 |
| `check_trending` | Get trending venues leaderboard | 3 |

## Message Format (API Contract)

### Request
```json
POST /agent/chat
{
  "message": "Find me a quiet bar in Wuse 2",
  "device_id": "uuid-from-flutter",
  "user_id": "supabase-user-id-if-logged-in",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

### Response
```json
{
  "reply": "I found 3 bars in Wuse 2...",
  "actions_performed": ["search_venues"],
  "actions_remaining_today": 8
}
```

## Context Injected into Every Request

Along with the user message, always inject:
```
You are Boki's assistant — a local guide for nightlife in Nigerian cities.
You help users discover bars, lounges, clubs, and restaurants.
Current city context: Abuja.
Today: {date}. Current time: {time} (WAT).
```
