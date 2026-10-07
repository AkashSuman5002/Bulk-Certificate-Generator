from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    certificate_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

    @field_validator("name", "certificate_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value