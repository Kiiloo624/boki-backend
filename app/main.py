from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Boki API",
    description="Backend API for Boki — nightlife discovery app",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


from app.api.routes import scraper, venues, reviews, chat, admin
app.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
app.include_router(venues.router, prefix="/venues", tags=["venues"])
app.include_router(reviews.router, prefix="/venues", tags=["reviews"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(admin.router, tags=["admin"])
