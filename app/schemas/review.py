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
