from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str  # Use service role for backend operations (not anon key)
    SUPABASE_ANON_KEY: str          # Used for verifying user JWTs

    # Google Gemini (AI agent)
    GEMINI_API_KEY: str

    # SerpApi (Google Maps scraping)
    SERPAPI_KEY: str

    # Google Maps (optional — using SerpApi instead for now)
    GOOGLE_MAPS_API_KEY: str = ""

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Admin routes protection
    ADMIN_API_KEY: str = ""

    # Rate limiting — max agent actions per user per 24h
    AGENT_DAILY_ACTION_LIMIT: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
