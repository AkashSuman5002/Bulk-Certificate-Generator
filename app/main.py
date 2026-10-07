from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.certificates import router as certificates_router
from app.api.routes.jobs import router as jobs_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(
    title="Bulk Certificate Generator API",
    version="1.0.0",
    description="Asynchronous bulk certificate generation with progress tracking.",
)
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(certificates_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}})


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    settings.logger.exception("Unhandled application error: %s", exc)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}})