# Boki API — Flutter Integration Reference

## Base URL

| Environment | URL |
|-------------|-----|
| Production  | `https://boki-backend.onrender.com` |
| Local dev   | `http://localhost:8000` |

Interactive docs (Swagger UI): `{base_url}/docs`

All responses are JSON. No authentication required for any public endpoint.

---

## Data Models

### VenueSummary
Returned in list responses.

```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",           // URL-safe unique identifier — use this for detail lookups
  "category": "string",       // see Category enum below
  "city": "string",           // always "Abuja" for now
  "district": "string|null",  // e.g. "Maitama", "Wuse 2", "Garki"
  "price_range": 1,           // int 1–4: 1=budget, 2=mid-range, 3=upscale, 4=luxury
  "google_rating": 4.5,       // float, nullable
  "google_reviews_count": 312, // int, nullable
  "is_verified": false,       // bool
  "cover_photo": {            // nullable — first item from photos array
    "url": "string",
    "source": "google"
  }
}
```

### VenueDetail
Returned by the single venue endpoint. Extends VenueSummary with:

```json
{
  // ...all VenueSummary fields, plus:
  "address": "string|null",
  "latitude": 9.0574,         // float, nullable
  "longitude": 7.4898,        // float, nullable
  "landmark_directions": "Opposite Transcorp Hilton, Maitama", // string|null — 97% coverage
  "phone": "+234 801 234 5678", // string|null
  "website": "string|null",
  "whatsapp": "string|null",
  "min_spend": "N10,000 per table", // string|null
  "camera_policy": "string|null",
  "age_restriction": "string|null",
  "opening_hours": "Open · Closes 2 AM", // string|null — raw text from Google
  "photos": [                 // array of photo objects
    { "url": "string", "source": "google" }
  ],
  "cover_photo": { "url": "string", "source": "google" }, // nullable
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

### VenueNearby
Returned by the nearby endpoint. Extends VenueSummary with:

```json
{
  // ...all VenueSummary fields, plus:
  "latitude": 9.0574,
  "longitude": 7.4898,
  "distance_km": 1.23        // float, sorted ascending
}
```

### Review

```json
{
  "id": "uuid",
  "author_name": "string",
  "rating": 5,               // int 1–5, nullable
  "body": "string",
  "source": "google",        // "google" | "tripadvisor" | "curated"
  "source_url": "string|null",
  "reviewed_at": "2024-06-01T00:00:00", // nullable
  "is_featured": true
}
```

### Paginated response wrapper
Used by `GET /venues` and `GET /venues/{slug}/reviews`:

```json
{
  "data": [...],
  "total": 469,   // total matching records (for pagination UI)
  "limit": 20,
  "offset": 0
}
```

### Category enum
```
bar | club | lounge | restaurant | rooftop | sports_bar |
hookah_lounge | entertainment | cinema | park | amusement_park | casino | other
```

### Price range
| Value | Label | Typical spend |
|-------|-------|--------------|
| 1 | Budget | under ₦5,000 |
| 2 | Mid-range | ₦5,000–15,000 |
| 3 | Upscale | ₦15,000–50,000 |
| 4 | Luxury | ₦50,000+ |

---

## Endpoints

### Health check
```
GET /health
```
Returns `{"status": "ok"}`. Use for connectivity checks.

---

### List venues
```
GET /venues
```

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `category` | string | — | Filter by category (exact match) |
| `district` | string | — | Filter by district (exact match) |
| `price_range` | int 1–4 | — | Filter by price range |
| `search` | string | — | Partial name match (case-insensitive) |
| `is_verified` | bool | — | Filter to verified venues only |
| `sort_by` | string | `google_rating` | `google_rating` \| `google_reviews_count` \| `name` \| `created_at` |
| `order` | string | `desc` | `asc` \| `desc` |
| `limit` | int | 20 | Max 100 |
| `offset` | int | 0 | For pagination |

**Response:** `VenueListResponse` (paginated VenueSummary)

**Examples:**
```
GET /venues                                          → top-rated venues
GET /venues?category=club&district=Maitama           → clubs in Maitama
GET /venues?price_range=3&sort_by=google_reviews_count → upscale, most reviewed
GET /venues?search=shisha&limit=10                   → name search
GET /venues?category=lounge&offset=20&limit=20       → page 2
```

---

### Get venue detail
```
GET /venues/{slug}
```

**Path param:** `slug` — from VenueSummary.slug

**Response:** `VenueDetail`

**Example:**
```
GET /venues/transcorp-hilton-abuja
```

**Errors:**
- `404` — venue not found or inactive

---

### Nearby venues (GPS)
```
GET /venues/nearby
```

**Query parameters:**

| Param | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `lat` | float | — | Yes | User latitude |
| `lng` | float | — | Yes | User longitude |
| `radius_km` | float | 5.0 | No | Search radius (0.5–50 km) |
| `limit` | int | 20 | No | Max 50 |

**Response:** `list[VenueNearby]` — sorted by `distance_km` ascending

**Example:**
```
GET /venues/nearby?lat=9.0574&lng=7.4898&radius_km=3
```

**Notes:**
- Returns an empty array (not 404) if no venues found within radius
- Use `radius_km=10` or higher if the user is outside central Abuja

---

### List districts
```
GET /venues/districts
```

**Response:** Array sorted by venue count descending
```json
[
  { "district": "Wuse 2", "count": 87 },
  { "district": "Maitama", "count": 64 },
  ...
]
```

---

### List categories
```
GET /venues/categories
```

**Response:** Array sorted by venue count descending
```json
[
  { "category": "restaurant", "count": 142 },
  { "category": "bar", "count": 98 },
  ...
]
```

---

### Venue reviews
```
GET /venues/{slug}/reviews
```

**Query parameters:**

| Param | Type | Default |
|-------|------|---------|
| `limit` | int | 20 (max 100) |
| `offset` | int | 0 |

**Response:** `ReviewListResponse` (paginated Review). Featured reviews are always returned first.

**Errors:**
- `404` — venue not found

---

### AI Chatbot
```
POST /chat
```

**Request body:**
```json
{
  "message": "Show me upscale clubs in Maitama",
  "history": [                          // optional — prior conversation turns
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:**
```json
{
  "reply": "Here are some upscale clubs in Maitama...",
  "venues": [                           // VenueDetail objects the AI fetched, may be empty
    { ...VenueDetail }
  ]
}
```

**Notes:**
- The client is responsible for maintaining `history` across turns — append each user message and assistant reply to the array and send it back on the next request
- `venues` contains the raw venue data the AI retrieved — use it to render venue cards alongside the reply
- Powered by Groq Llama 4 Scout; typical latency 1–3 seconds
- No rate limiting currently — add client-side debounce

**Conversation management pattern (Flutter):**
```dart
List<Map<String, String>> history = [];

Future<ChatResponse> sendMessage(String message) async {
  final response = await http.post(
    Uri.parse('$baseUrl/chat'),
    body: jsonEncode({ 'message': message, 'history': history }),
  );
  final data = jsonDecode(response.body);
  // Append to history for next turn
  history.add({ 'role': 'user', 'content': message });
  history.add({ 'role': 'assistant', 'content': data['reply'] });
  return ChatResponse.fromJson(data);
}
```

---

## Error responses

All errors follow FastAPI's default shape:
```json
{ "detail": "Venue not found" }
```

| Status | Meaning |
|--------|---------|
| 404 | Resource not found |
| 422 | Validation error (invalid query param type/range) |
| 500 | Server error (includes upstream AI/DB errors) |

---

## Pagination pattern

```dart
// First page
GET /venues?limit=20&offset=0   → total: 469
// Second page
GET /venues?limit=20&offset=20
// Last page check: offset + limit >= total
```

---

## Notes for Flutter integration

- **Slugs are stable** — safe to deep-link and cache locally against a slug key
- **`cover_photo.url`** — direct Google Maps CDN URLs; load with `Image.network()`, no auth needed
- **`opening_hours`** — raw string from Google (e.g. `"Open · Closes 2 AM"`), not structured — display as-is
- **`photos` array** — can be empty; always check before accessing index 0 (use `cover_photo` instead)
- **`price_range` null** — a small number of venues have no price inference yet; handle gracefully
- **Offline cache** — `address`, `landmark_directions`, `phone`, `opening_hours` from VenueDetail are the fields worth caching for offline use
- **`/venues/nearby` ordering** — `GET /venues/districts` and `GET /venues/categories` are good candidates to fetch on app launch and cache for filter UI
