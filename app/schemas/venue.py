from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime
import uuid


class VenueSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: str
    city: str
    district: Optional[str] = None
    price_range: Optional[int] = None
    google_rating: Optional[float] = None
    google_reviews_count: Optional[int] = None
    is_verified: bool
    cover_photo: Optional[dict] = None


class VenueDetail(VenueSummary):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark_directions: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    min_spend: Optional[str] = None
    camera_policy: Optional[str] = None
    age_restriction: Optional[str] = None
    photos: list = []
    opening_hours: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class VenueNearby(VenueSummary):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: float


class DistrictCount(BaseModel):
    district: str
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int


class VenueListResponse(BaseModel):
    data: List[VenueSummary]
    total: int
    limit: int
    offset: int
