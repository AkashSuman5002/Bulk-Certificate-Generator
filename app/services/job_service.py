import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Certificate, CertificateStatus, GenerationJob, JobStatus
from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_job(db: Session, payload: JobCreate) -> GenerationJob:
    job = GenerationJob(
        event_name=payload.event_name, event_date=payload.event_date,
        organization_name=payload.organization_name, signatory_name=payload.signatory_name,
        total_count=len(payload.recipients), status=JobStatus.pending,
    )
    job.certificates = [Certificate(certificate_id=r.certificate_id, recipient_name=r.name, recipient_email=str(r.email)) for r in payload.recipients]
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("job created id=%s total=%s", job.id, job.total_count)
    return job


def get_job(db: Session, job_id: UUID) -> GenerationJob | None:
    return db.get(GenerationJob, job_id)


def job_progress(job: GenerationJob) -> dict[str, int | str | UUID | datetime | None]:
    completed = job.successful_count + job.failed_count
    pending = max(job.total_count - completed, 0)
    progress = min(100, int(completed * 100 / job.total_count)) if job.total_count else 100
    return {"job_id": job.id, "status": job.status.value, "total": job.total_count, "successful": job.successful_count, "failed": job.failed_count, "pending": pending, "progress_percentage": progress, "created_at": job.created_at, "started_at": job.started_at, "completed_at": job.completed_at}


def process_job(db: Session, job_id: UUID) -> None:
    from app.services.certificate_service import generate_certificate

    job = get_job(db, job_id)
    if job is None:
        logger.error("background job missing id=%s", job_id)
        return
    job.status = JobStatus.processing
    job.started_at = utcnow()
    db.commit()
    logger.info("job started id=%s", job_id)
    for certificate in list(job.certificates):
        try:
            logger.info("certificate generation started job=%s certificate=%s", job_id, certificate.certificate_id)
            path = generate_certificate(job, certificate.certificate_id, certificate.recipient_name)
            certificate.status = CertificateStatus.completed
            certificate.file_path = str(path)
            certificate.completed_at = utcnow()
            job.successful_count += 1
            logger.info("certificate generation succeeded job=%s certificate=%s", job_id, certificate.certificate_id)
        except Exception as exc:
            db.rollback()
            certificate = db.get(Certificate, certificate.id)
            job = db.get(GenerationJob, job_id)
            certificate.status = CertificateStatus.failed
            certificate.error_message = str(exc)[:1000]
            certificate.completed_at = utcnow()
            job.failed_count += 1
            logger.exception("certificate generation failed job=%s certificate=%s", job_id, certificate.certificate_id)
        db.commit()
    job = db.get(GenerationJob, job_id)
    job.status = JobStatus.completed_with_errors if job.failed_count else JobStatus.completed
    job.completed_at = utcnow()
    db.commit()
    logger.info("job completed id=%s status=%s", job_id, job.status.value)