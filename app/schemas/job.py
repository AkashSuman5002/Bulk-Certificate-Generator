from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.recipient import RecipientCreate


class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    event_date: date
    organization_name: str = Field(min_length=1, max_length=200)
    signatory_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientCreate] = Field(min_length=1, max_length=1000)

    @field_validator("event_name", "organization_name", "signatory_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def unique_certificate_ids(self) -> "JobCreate":
        ids = [recipient.certificate_id for recipient in self.recipients]
        if len(ids) != len(set(ids)):
            raise ValueError("certificate_id values must be unique within a job")
        return self


class JobCreated(BaseModel):
    job_id: UUID
    status: str
    total: int
    message: str


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    total: int
    successful: int
    failed: int
    pending: int
    progress_percentage: int
    created_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class CertificateItem(BaseModel):
    certificate_id: str
    recipient_name: str
    email: str
    status: str
    download_url: str | None
    error_message: str | None = None


class CertificatePage(BaseModel):
    job_id: UUID
    items: list[CertificateItem]
    page: int
    page_size: int
    total: int