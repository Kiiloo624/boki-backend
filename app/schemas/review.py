from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class ReviewOut(BaseModel):
    id: uuid.UUID
    author_name: str
    rating: Optional[int] = None
    body: str
    source: str
    source_url: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    is_featured: bool


class ReviewListResponse(BaseModel):
    data: List[ReviewOut]
    total: int
    limit: int
    offset: int


class ReviewCreate(BaseModel):
    venue_slug: str
    author_name: str
    rating: int  # 1-5
    body: str
    source: str = "curated"
    source_url: Optional[str] = None
    reviewed_at: Optional[str] = None  # ISO date string
    is_featured: bool = False


class ReviewUpdate(BaseModel):
    is_featured: Optional[bool] = None
    body: Optional[str] = None
    rating: Optional[int] = None
    author_name: Optional[str] = None
