# Admin API Endpoints — Backend Spec

> These endpoints are required by the Boki Admin Dashboard (`boki-admin`).  
> All must be protected by the existing `require_admin_key` dependency (`app/api/deps.py`).  
> Add them under a new router prefix `/admin` in a new file `app/api/routes/admin.py`.

---

## Authentication

All endpoints use the existing `X-Admin-Key` header check:

```python
# app/api/routes/admin.py
from app.api.deps import require_admin_key

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_key)])
```

---

## 1. Stats — Dashboard

### `GET /admin/stats`

Returns aggregate counts for the admin dashboard.

**Response:**
```json
{
  "total_venues": 469,
  "verified_venues": 312,
  "active_venues": 450,
  "inactive_venues": 19,
  "total_reviews": 2840,
  "venues_with_website": 401,
  "venues_with_price_range": 421,
  "venues_with_landmark_directions": 454,
  "venues_with_photos": 469,
  "venues_by_category": [
    { "category": "Restaurant", "count": 120 },
    { "category": "Bar", "count": 98 }
  ],
  "venues_by_district": [
    { "district": "Wuse 2", "count": 67 },
    { "district": "Maitama", "count": 54 }
  ]
}
```

**Implementation notes:**
- Run aggregation queries on the `venues` table via the Supabase service-role client
- `venues_with_X` counts rows where that column is not null/empty
- `venues_by_category` and `venues_by_district`: use Supabase `.select('category').eq(...)` or raw SQL count with group by

---

## 2. Venues — Write Endpoints

The existing `GET /venues` and `GET /venues/{slug}` endpoints are reused for reads.

### `POST /admin/venues`

Create a venue manually.

**Request body** (`VenueCreate` schema):
```json
{
  "name": "Zinc Lounge",
  "category": "Bar",
  "city": "Abuja",
  "district": "Wuse 2",
  "address": "Plot 1234 Aminu Kano Crescent, Wuse 2",
  "latitude": 9.0765,
  "longitude": 7.4983,
  "landmark_directions": "Next to Transcorp Hilton, opposite GTBank",
  "phone": "+2348012345678",
  "website": "https://zinclounge.com",
  "whatsapp": "+2348012345678",
  "instagram_handle": "zinclounge",
  "price_range": 3,
  "min_spend": 5000,
  "camera_policy": "Allowed",
  "age_restriction": "18+",
  "photos": ["https://..."],
  "opening_hours": {
    "monday": "12:00-23:00",
    "tuesday": "12:00-23:00"
  },
  "is_verified": false,
  "is_active": true
}
```

All fields optional except `name`, `category`, `city`, `district`.

**Response:** `VenueDetail` (201 Created)

**Implementation notes:**
- Auto-generate `slug` from `name` (slugify, check uniqueness, append `-2` etc. if taken)
- Insert into `venues` table via Supabase service-role client
- `google_place_id` will be null for manually created venues

---

### `PATCH /admin/venues/{slug}`

Update any venue fields. Partial update (only provided fields are changed).

**Request body** (`VenueUpdate` schema — all fields optional):
```json
{
  "name": "Zinc Lounge Abuja",
  "price_range": 4,
  "is_verified": true,
  "landmark_directions": "Updated directions..."
}
```

**Response:** `VenueDetail` (200 OK)

**Implementation notes:**
- Use `.update(data).eq('slug', slug)` on Supabase
- If `name` changes and `slug` should follow, regenerate slug (optional — discuss with team)
- Return the full updated venue detail

---

### `DELETE /admin/venues/{slug}`

Soft-delete a venue by setting `is_active = false`, or hard-delete if `permanent=true`.

**Query params:**
- `permanent` (bool, default `false`) — if true, deletes the row permanently

**Response:** `204 No Content`

**Implementation notes:**
- Default: set `is_active = false` (safe, reversible)
- `permanent=true`: `.delete().eq('slug', slug)` — also deletes associated reviews (cascade or manual)

---

### `PATCH /admin/venues/{slug}/photos`

Update the photos array for a venue (called after uploading to Supabase Storage).

**Request body:**
```json
{
  "photos": [
    "https://your-project.supabase.co/storage/v1/object/public/venue-photos/slug/photo1.jpg",
    "https://your-project.supabase.co/storage/v1/object/public/venue-photos/slug/photo2.jpg"
  ]
}
```

**Response:** `{ "photos": [...] }` (200 OK)

**Implementation notes:**
- Replaces the entire `photos` JSONB array (ordering is preserved from the array)
- The admin frontend handles the actual Supabase Storage upload directly; this endpoint only updates the DB record

---

## 3. Reviews — Write Endpoints

The existing `GET /venues/{slug}/reviews` is reused for reads.

### `GET /admin/reviews`

List all reviews across all venues (admin view, not tied to a specific venue).

**Query params:**
- `venue_slug` (optional) — filter by venue
- `source` (optional) — `google` | `tripadvisor` | `curated`
- `is_featured` (optional, bool)
- `rating` (optional, int 1–5)
- `page` (default 1), `page_size` (default 25)

**Response:**
```json
{
  "items": [ ...ReviewOut... ],
  "total": 2840,
  "page": 1,
  "page_size": 25
}
```

---

### `POST /admin/reviews`

Add a manually curated review.

**Request body:**
```json
{
  "venue_slug": "zinc-lounge",
  "author_name": "Boki Team",
  "rating": 5,
  "body": "Amazing rooftop views and great cocktails...",
  "source": "curated",
  "source_url": null,
  "reviewed_at": "2026-04-01",
  "is_featured": true
}
```

**Response:** `ReviewOut` (201 Created)

---

### `PATCH /admin/reviews/{id}`

Update a review (toggle featured, edit body, etc.).

**Request body** (all optional):
```json
{
  "is_featured": true,
  "body": "Updated review text",
  "rating": 4
}
```

**Response:** `ReviewOut` (200 OK)

---

### `DELETE /admin/reviews/{id}`

Permanently delete a review.

**Response:** `204 No Content`

---

## 4. Schemas to Add

Add to `app/schemas/venue.py`:

```python
class VenueCreate(BaseModel):
    name: str
    category: str
    city: str
    district: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    landmark_directions: str | None = None
    phone: str | None = None
    website: str | None = None
    whatsapp: str | None = None
    instagram_handle: str | None = None
    price_range: int | None = None  # 1-4
    min_spend: int | None = None
    camera_policy: str | None = None
    age_restriction: str | None = None
    photos: list[str] = []
    opening_hours: dict | None = None
    is_verified: bool = False
    is_active: bool = True

class VenueUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    district: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    landmark_directions: str | None = None
    phone: str | None = None
    website: str | None = None
    whatsapp: str | None = None
    instagram_handle: str | None = None
    price_range: int | None = None
    min_spend: int | None = None
    camera_policy: str | None = None
    age_restriction: str | None = None
    opening_hours: dict | None = None
    is_verified: bool | None = None
    is_active: bool | None = None

class VenuePhotosUpdate(BaseModel):
    photos: list[str]

class AdminStats(BaseModel):
    total_venues: int
    verified_venues: int
    active_venues: int
    inactive_venues: int
    total_reviews: int
    venues_with_website: int
    venues_with_price_range: int
    venues_with_landmark_directions: int
    venues_with_photos: int
    venues_by_category: list[dict]
    venues_by_district: list[dict]
```

Add to `app/schemas/review.py`:

```python
class ReviewCreate(BaseModel):
    venue_slug: str
    author_name: str
    rating: int  # 1-5
    body: str
    source: str = "curated"
    source_url: str | None = None
    reviewed_at: str | None = None  # ISO date string
    is_featured: bool = False

class ReviewUpdate(BaseModel):
    is_featured: bool | None = None
    body: str | None = None
    rating: int | None = None
    author_name: str | None = None
```

---

## 5. Supabase Storage Setup

Create a public storage bucket named `venue-photos`:

```sql
-- In Supabase dashboard or migration
insert into storage.buckets (id, name, public)
values ('venue-photos', 'venue-photos', true);
```

RLS policy (allow service role to do everything, public to read):
```sql
create policy "Public read" on storage.objects
  for select using (bucket_id = 'venue-photos');

create policy "Service role write" on storage.objects
  for all using (auth.role() = 'service_role');
```

Photo URL pattern: `{SUPABASE_URL}/storage/v1/object/public/venue-photos/{venue_slug}/{filename}`

---

## 6. Register the Router

In `app/main.py`, add:

```python
from app.api.routes import admin

app.include_router(admin.router)
```

---

## Summary of New Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/admin/stats` | Admin key | Dashboard aggregate stats |
| POST | `/admin/venues` | Admin key | Create venue manually |
| PATCH | `/admin/venues/{slug}` | Admin key | Update venue fields |
| DELETE | `/admin/venues/{slug}` | Admin key | Soft/hard delete venue |
| PATCH | `/admin/venues/{slug}/photos` | Admin key | Update photos array |
| GET | `/admin/reviews` | Admin key | List all reviews (cross-venue) |
| POST | `/admin/reviews` | Admin key | Add curated review |
| PATCH | `/admin/reviews/{id}` | Admin key | Update review |
| DELETE | `/admin/reviews/{id}` | Admin key | Delete review |
