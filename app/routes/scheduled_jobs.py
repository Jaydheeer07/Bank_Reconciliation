from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.scheduled_tasks.job_manager import stop_job

router = APIRouter(prefix="/scheduled")


@router.post("/stop-processing/{job_id}")
async def stop_processing(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Stop a scheduled processing job"""
    return await stop_job(db, job_id)
