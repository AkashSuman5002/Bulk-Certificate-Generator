from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.db.models import Certificate, GenerationJob
from app.schemas.job import CertificateItem, CertificatePage, JobCreate, JobCreated, JobStatusResponse
from app.services.job_service import create_job, get_job, job_progress, process_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def run_background_job(job_id: UUID) -> None:
    db = SessionLocal()
    try:
        process_job(db, job_id)
    finally:
        db.close()


@router.post("", response_model=JobCreated, status_code=status.HTTP_202_ACCEPTED)
def create_generation_job(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> JobCreated:
    job = create_job(db, payload)
    background_tasks.add_task(run_background_job, job.id)
    return JobCreated(job_id=job.id, status=job.status.value, total=job.total_count, message="Certificate generation job created")


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_generation_job(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusResponse | JSONResponse:
    job = get_job(db, job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": {"code": "JOB_NOT_FOUND", "message": "Generation job not found"}})
    return JobStatusResponse(**job_progress(job))


@router.get("/{job_id}/certificates", response_model=CertificatePage)
def list_job_certificates(
    job_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> CertificatePage | JSONResponse:
    if get_job(db, job_id) is None:
        return JSONResponse(status_code=404, content={"error": {"code": "JOB_NOT_FOUND", "message": "Generation job not found"}})
    total = db.scalar(select(func.count()).select_from(Certificate).where(Certificate.job_id == job_id)) or 0
    items = db.scalars(select(Certificate).where(Certificate.job_id == job_id).order_by(Certificate.created_at).offset((page - 1) * page_size).limit(page_size)).all()
    return CertificatePage(
        job_id=job_id,
        items=[CertificateItem(certificate_id=item.certificate_id, recipient_name=item.recipient_name, email=item.recipient_email, status=item.status.value, download_url=f"/api/v1/certificates/{item.id}/download" if item.status.value == "completed" else None, error_message=item.error_message) for item in items],
        page=page, page_size=page_size, total=total,
    )