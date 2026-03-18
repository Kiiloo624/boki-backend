import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.services.scraper.pipeline import scrape_and_save, DEFAULT_QUERIES
from app.services.scraper.enricher import enrich_venues
from app.services.scraper.price_inferencer import infer_price_ranges
from app.services.scraper.landmark_inferencer import infer_landmark_directions
from app.api.deps import require_admin_key

router = APIRouter(dependencies=[Depends(require_admin_key)])

# In-memory job store — fine for a single-instance deployment
_jobs: dict[str, dict] = {}


def _get_job(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@router.post("/run")
async def run_scraper(background_tasks: BackgroundTasks, queries: list[str] | None = None):
    """
    Kick off a scrape run in the background. Returns a job_id immediately.
    Poll GET /scraper/status/{job_id} for results.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "result": None}

    async def _run():
        try:
            result = await scrape_and_save(queries or DEFAULT_QUERIES)
            _jobs[job_id] = {"status": "done", "result": result}
        except Exception as e:
            _jobs[job_id] = {"status": "error", "result": str(e)}

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "running"}


@router.post("/enrich")
async def run_enricher(background_tasks: BackgroundTasks, limit: int = 20):
    """Enrich venues with websites via Gemini extraction. Runs in the background."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "result": None}

    async def _run():
        try:
            result = await enrich_venues(limit=limit)
            _jobs[job_id] = {"status": "done", "result": result}
        except Exception as e:
            _jobs[job_id] = {"status": "error", "result": str(e)}

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "running"}


@router.post("/infer-prices")
async def run_price_inferencer(background_tasks: BackgroundTasks, limit: int | None = None):
    """Infer price_range (1–4) for venues via Gemini. Runs in the background."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "result": None}

    async def _run():
        try:
            result = await infer_price_ranges(limit=limit)
            _jobs[job_id] = {"status": "done", "result": result}
        except Exception as e:
            _jobs[job_id] = {"status": "error", "result": str(e)}

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "running"}


@router.post("/infer-landmarks")
async def run_landmark_inferencer(background_tasks: BackgroundTasks, limit: int | None = None):
    """Infer landmark_directions for venues via Gemini. Runs in the background."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "result": None}

    async def _run():
        try:
            result = await infer_landmark_directions(limit=limit)
            _jobs[job_id] = {"status": "done", "result": result}
        except Exception as e:
            _jobs[job_id] = {"status": "error", "result": str(e)}

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "running"}


@router.get("/status/{job_id}")
async def job_status(job_id: str):
    """Check the status of a background scraper job."""
    return _get_job(job_id)
