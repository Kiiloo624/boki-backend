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
    instagram_handle: Optional[str] = None
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


class VenueCreate(BaseModel):
    name: str
    category: str
    city: str
    district: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark_directions: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram_handle: Optional[str] = None
    price_range: Optional[int] = None  # 1-4
    min_spend: Optional[int] = None
    camera_policy: Optional[str] = None
    age_restriction: Optional[str] = None
    photos: list = []
    opening_hours: Optional[Any] = None
    is_verified: bool = False
    is_active: bool = True


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark_directions: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram_handle: Optional[str] = None
    price_range: Optional[int] = None
    min_spend: Optional[int] = None
    camera_policy: Optional[str] = None
    age_restriction: Optional[str] = None
    opening_hours: Optional[Any] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class VenuePhotosUpdate(BaseModel):
    photos: List[str]


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
    venues_by_category: List[dict]
    venues_by_district: List[dict]
