from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.db.models import GenerationJob
from app.templates.certificate_template import render_certificate


def certificate_path(job_id: UUID, certificate_id: str) -> Path:
    job_dir = (settings.generated_certificates_dir / str(job_id)).resolve()
    job_dir.mkdir(parents=True, exist_ok=True)
    path = (job_dir / f"{certificate_id}.pdf").resolve()
    if job_dir not in path.parents:
        raise ValueError("invalid certificate path")
    return path


def generate_certificate(job: GenerationJob, certificate_id: str, recipient_name: str) -> Path:
    path = certificate_path(job.id, certificate_id)
    pdf_bytes = render_certificate(
        organization_name=job.organization_name,
        event_name=job.event_name,
        event_date=job.event_date,
        recipient_name=recipient_name,
        certificate_id=certificate_id,
        signatory_name=job.signatory_name,
    )
    path.write_bytes(pdf_bytes)
    return path