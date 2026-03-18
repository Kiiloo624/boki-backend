from fastapi import Header, HTTPException
from app.core.config import settings


def require_admin_key(x_admin_key: str = Header(...)):
    if not settings.ADMIN_API_KEY or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
