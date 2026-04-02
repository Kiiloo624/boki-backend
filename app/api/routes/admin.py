import re
import unicodedata
import uuid
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_admin_key
from app.core.supabase import supabase
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from app.schemas.venue import (
    AdminStats,
    VenueCreate,
    VenueDetail,
    VenuePhotosUpdate,
    VenueUpdate,
)

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_key)])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _unique_slug(name: str) -> str:
    base = _slugify(name)
    slug = base
    counter = 2
    while True:
        existing = supabase.table("venues").select("id").eq("slug", slug).execute()
        if not existing.data:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def _venue_row_to_detail(row: dict) -> dict:
    row["cover_photo"] = row["photos"][0] if row.get("photos") else None
    return row


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=AdminStats)
async def get_stats():
    """Aggregate counts for the admin dashboard."""
    venues_resp = supabase.table("venues").select("*").execute()
    venues = venues_resp.data or []

    reviews_resp = supabase.table("venue_reviews").select("id", count="exact").execute()
    total_reviews = reviews_resp.count or 0

    by_category = Counter(v["category"] for v in venues if v.get("category"))
    by_district = Counter(v["district"] for v in venues if v.get("district"))

    return AdminStats(
        total_venues=len(venues),
        verified_venues=sum(1 for v in venues if v.get("is_verified")),
        active_venues=sum(1 for v in venues if v.get("is_active")),
        inactive_venues=sum(1 for v in venues if not v.get("is_active")),
        total_reviews=total_reviews,
        venues_with_website=sum(1 for v in venues if v.get("website")),
        venues_with_price_range=sum(1 for v in venues if v.get("price_range") is not None),
        venues_with_landmark_directions=sum(1 for v in venues if v.get("landmark_directions")),
        venues_with_photos=sum(1 for v in venues if v.get("photos")),
        venues_by_category=[{"category": c, "count": n} for c, n in by_category.most_common()],
        venues_by_district=[{"district": d, "count": n} for d, n in by_district.most_common()],
    )


# ---------------------------------------------------------------------------
# Venues — write
# ---------------------------------------------------------------------------

@router.post("/venues", response_model=VenueDetail, status_code=201)
async def create_venue(body: VenueCreate):
    """Create a venue manually."""
    slug = _unique_slug(body.name)
    data = body.model_dump()
    data["slug"] = slug

    resp = supabase.table("venues").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create venue")

    return _venue_row_to_detail(resp.data[0])


@router.patch("/venues/{slug}", response_model=VenueDetail)
async def update_venue(slug: str, body: VenueUpdate):
    """Partial update of a venue."""
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="No fields to update")

    resp = (
        supabase.table("venues")
        .update(data)
        .eq("slug", slug)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Venue not found")

    return _venue_row_to_detail(resp.data[0])


@router.delete("/venues/{slug}", status_code=204)
async def delete_venue(slug: str, permanent: bool = Query(False)):
    """Soft-delete (default) or permanently delete a venue."""
    if permanent:
        supabase.table("venues").delete().eq("slug", slug).execute()
    else:
        resp = (
            supabase.table("venues")
            .update({"is_active": False})
            .eq("slug", slug)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Venue not found")


@router.patch("/venues/{slug}/photos")
async def update_venue_photos(slug: str, body: VenuePhotosUpdate):
    """Replace the photos array for a venue."""
    resp = (
        supabase.table("venues")
        .update({"photos": body.photos})
        .eq("slug", slug)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Venue not found")

    return {"photos": resp.data[0]["photos"]}


# ---------------------------------------------------------------------------
# Reviews — write
# ---------------------------------------------------------------------------

@router.get("/reviews")
async def list_reviews(
    venue_slug: Optional[str] = None,
    source: Optional[str] = None,
    is_featured: Optional[bool] = None,
    rating: Optional[int] = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """List all reviews across venues (admin view)."""
    offset = (page - 1) * page_size

    # Resolve venue_slug → venue_id if needed
    venue_id: Optional[str] = None
    if venue_slug:
        v = supabase.table("venues").select("id").eq("slug", venue_slug).maybe_single().execute()
        if not v.data:
            raise HTTPException(status_code=404, detail="Venue not found")
        venue_id = v.data["id"]

    query = supabase.table("venue_reviews").select(
        "id, author_name, rating, body, source, source_url, reviewed_at, is_featured",
        count="exact",
    )

    if venue_id:
        query = query.eq("venue_id", venue_id)
    if source:
        query = query.eq("source", source)
    if is_featured is not None:
        query = query.eq("is_featured", is_featured)
    if rating is not None:
        query = query.eq("rating", rating)

    query = (
        query
        .order("is_featured", desc=True)
        .order("reviewed_at", desc=True, nullsfirst=False)
        .range(offset, offset + page_size - 1)
    )
    resp = query.execute()

    return {
        "items": resp.data or [],
        "total": resp.count or 0,
        "page": page,
        "page_size": page_size,
    }


@router.post("/reviews", response_model=ReviewOut, status_code=201)
async def create_review(body: ReviewCreate):
    """Add a manually curated review."""
    v = (
        supabase.table("venues")
        .select("id")
        .eq("slug", body.venue_slug)
        .maybe_single()
        .execute()
    )
    if not v.data:
        raise HTTPException(status_code=404, detail="Venue not found")

    data = body.model_dump(exclude={"venue_slug"})
    data["venue_id"] = v.data["id"]

    resp = supabase.table("venue_reviews").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create review")

    return resp.data[0]


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
async def update_review(review_id: uuid.UUID, body: ReviewUpdate):
    """Update a review (toggle featured, edit body, etc.)."""
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="No fields to update")

    resp = (
        supabase.table("venue_reviews")
        .update(data)
        .eq("id", str(review_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Review not found")

    return resp.data[0]


@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: uuid.UUID):
    """Permanently delete a review."""
    supabase.table("venue_reviews").delete().eq("id", str(review_id)).execute()
