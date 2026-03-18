from fastapi import APIRouter, HTTPException, Query
from app.core.supabase import supabase
from app.schemas.review import ReviewOut, ReviewListResponse

router = APIRouter()


@router.get("/{slug}/reviews", response_model=ReviewListResponse)
async def list_reviews(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Paginated reviews for a venue. Featured reviews are returned first."""
    venue_resp = (
        supabase.table("venues")
        .select("id")
        .eq("slug", slug)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not venue_resp.data:
        raise HTTPException(status_code=404, detail="Venue not found")

    venue_id = venue_resp.data["id"]

    response = (
        supabase.table("venue_reviews")
        .select(
            "id, author_name, rating, body, source, source_url, reviewed_at, is_featured",
            count="exact",
        )
        .eq("venue_id", venue_id)
        .order("is_featured", desc=True)
        .order("reviewed_at", desc=True, nullsfirst=False)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return ReviewListResponse(
        data=response.data,
        total=response.count or 0,
        limit=limit,
        offset=offset,
    )
