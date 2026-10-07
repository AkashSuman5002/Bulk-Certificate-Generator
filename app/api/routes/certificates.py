from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Certificate, CertificateStatus

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/{certificate_id}/download", response_class=FileResponse, response_model=None)
def download_certificate(certificate_id: UUID, db: Session = Depends(get_db)) -> FileResponse | JSONResponse:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None:
        return JSONResponse(status_code=404, content={"error": {"code": "CERTIFICATE_NOT_FOUND", "message": "Certificate not found"}})
    if certificate.status != CertificateStatus.completed or not certificate.file_path:
        return JSONResponse(status_code=409, content={"error": {"code": "CERTIFICATE_NOT_READY", "message": certificate.error_message or "Certificate generation failed or is not complete"}})
    root = settings.generated_certificates_dir.resolve()
    path = Path(certificate.file_path).resolve()
    if root not in path.parents or not path.is_file():
        return JSONResponse(status_code=404, content={"error": {"code": "CERTIFICATE_FILE_NOT_FOUND", "message": "Generated certificate file not found"}})
    return FileResponse(path=path, media_type="application/pdf", filename=f"{certificate.certificate_id}.pdf")