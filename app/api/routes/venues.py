from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal
from collections import Counter
from app.core.supabase import supabase
from app.schemas.venue import (
    VenueSummary, VenueDetail, VenueListResponse, DistrictCount, CategoryCount
)

router = APIRouter()


@router.get("/districts", response_model=list[DistrictCount])
async def list_districts():
    """All Abuja districts that have active venues, sorted by venue count."""
    response = supabase.table("venues").select("district").eq("is_active", True).execute()
    counts = Counter(r["district"] for r in response.data if r.get("district"))
    return [{"district": d, "count": c} for d, c in counts.most_common()]


@router.get("/categories", response_model=list[CategoryCount])
async def list_categories():
    """All venue categories with active venue counts."""
    response = supabase.table("venues").select("category").eq("is_active", True).execute()
    counts = Counter(r["category"] for r in response.data if r.get("category"))
    return [{"category": c, "count": n} for c, n in counts.most_common()]


@router.get("", response_model=VenueListResponse)
async def list_venues(
    category: Optional[str] = None,
    district: Optional[str] = None,
    price_range: Optional[int] = Query(None, ge=1, le=4),
    search: Optional[str] = None,
    is_verified: Optional[bool] = None,
    sort_by: Literal["google_rating", "google_reviews_count", "name", "created_at"] = "google_rating",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List venues with optional filters, sorting, and pagination.

    - **category**: filter by venue category (e.g. `bar`, `club`, `lounge`)
    - **district**: filter by Abuja district (e.g. `Maitama`, `Wuse 2`)
    - **price_range**: 1 (₦) to 4 (₦₦₦₦)
    - **search**: partial name match
    - **sort_by**: `google_rating` | `google_reviews_count` | `name` | `created_at`
    """
    query = (
        supabase.table("venues")
        .select(
            "id, name, slug, category, city, district, price_range, "
            "google_rating, google_reviews_count, is_verified, photos",
            count="exact",
        )
        .eq("is_active", True)
    )

    if category:
        query = query.eq("category", category)
    if district:
        query = query.eq("district", district)
    if price_range is not None:
        query = query.eq("price_range", price_range)
    if search:
        query = query.ilike("name", f"%{search}%")
    if is_verified is not None:
        query = query.eq("is_verified", is_verified)

    query = query.order(sort_by, desc=(order == "desc")).range(offset, offset + limit - 1)
    response = query.execute()

    venues = [
        {**row, "cover_photo": row["photos"][0] if row.get("photos") else None}
        for row in response.data
    ]

    return VenueListResponse(
        data=venues,
        total=response.count or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{slug}", response_model=VenueDetail)
async def get_venue(slug: str):
    """Full detail for a single venue by its slug."""
    response = (
        supabase.table("venues")
        .select("*")
        .eq("slug", slug)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Venue not found")

    row = response.data
    row["cover_photo"] = row["photos"][0] if row.get("photos") else None
    return row
