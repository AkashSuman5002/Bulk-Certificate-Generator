# Bulk Certificate Generator API

## Project Overview

A FastAPI backend that accepts a bulk certificate request, validates recipients, creates a tracked generation job, generates one PDF per recipient, and exposes progress and secure downloads.

## Features

- Asynchronous bulk jobs using FastAPI `BackgroundTasks`
- Pydantic v2 validation for recipient data and duplicate certificate IDs
- PostgreSQL persistence with SQLAlchemy 2.x and Alembic
- Per-recipient success/failure tracking and failure isolation
- Professional predefined ReportLab certificate template
- Paginated certificate results and safe PDF downloads
- Structured logging, health endpoint, OpenAPI docs, Docker Compose
- Deterministic SQLite-backed tests without a production database

## Tech Stack

Python 3.12+, FastAPI, Uvicorn, PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, ReportLab, pytest, httpx.

The requirements constrain Starlette to the compatible pre-1.0 line because Starlette 1.x emits an upstream deprecation warning when its `TestClient` falls back to `httpx`; the assignment explicitly requires `httpx`, and application behavior is unchanged by this compatibility constraint.

## Architecture

`app/api` handles HTTP contracts, `app/schemas` validates input and output, `app/services` owns job and file behavior, `app/db` owns persistence, `app/templates` renders PDFs, and the worker is invoked through FastAPI background tasks. PostgreSQL is the production database; tests inject an in-memory SQLite session.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.12 -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` in `.env` to a reachable PostgreSQL instance. No secrets are committed.

## Database Setup

```powershell
alembic upgrade head
```

Create future migrations with `alembic revision --autogenerate -m "describe change"`, review the generated migration, then apply it with `alembic upgrade head`.

## Running Locally

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive documentation is at `/docs`; alternative documentation is at `/redoc`; health is at `/health`.

## Running With Docker

```powershell
docker compose up --build
```

The Compose stack starts PostgreSQL and the API. Run migrations from the API container with `docker compose exec api alembic upgrade head`.

## Running Tests

```powershell
py -3.12 -m pytest
```

Tests use an isolated in-memory SQLite database and do not require PostgreSQL.

## API Endpoints

- `POST /api/v1/jobs` creates a job and returns HTTP 202.
- `GET /api/v1/jobs/{job_id}` returns counts, status, and bounded progress.
- `GET /api/v1/jobs/{job_id}/certificates?page=1&page_size=20` returns paginated certificate records.
- `GET /api/v1/certificates/{certificate_id}/download` streams a completed PDF.

### Example Create Job Request

```powershell
curl -X POST http://localhost:8000/api/v1/jobs -H "Content-Type: application/json" --data-binary "@examples/create_job.json"
```

Example response:

```json
{"job_id":"8c6f...","status":"pending","total":5,"message":"Certificate generation job created"}
```

### Job Status Response

```json
{"job_id":"8c6f...","status":"completed_with_errors","total":5,"successful":4,"failed":1,"pending":0,"progress_percentage":100,"created_at":"2026-10-07T10:00:00Z","started_at":"2026-10-07T10:00:00Z","completed_at":"2026-10-07T10:00:02Z"}
```

## Error Handling

Validation failures return 422 with an `error` object. Missing jobs and certificates return 404. Failed or incomplete certificate downloads return 409. Internal errors are logged without exposing stack traces.

## Bulk Processing and Failure Isolation

The API inserts the job and pending certificate rows in one transaction, returns immediately, and schedules one background task. The worker commits each recipient independently inside its own `try/except` boundary. A failed PDF records an error and increments `failed_count`; subsequent recipients continue. Final status is `completed`, `completed_with_errors`, or `failed`. `BackgroundTasks` is intentionally simple for this assignment; a durable queue such as Celery/RQ with Redis would be appropriate for distributed workers and restart-safe delivery.

## Database Design

`generation_jobs` stores request metadata, lifecycle timestamps, aggregate counts, and status. `certificates` stores recipient data, certificate status, safe relative-to-root file metadata, and errors. A foreign key links certificates to jobs, `(job_id, certificate_id)` is unique, and indexes support status and job listing queries.

## Certificate Generation Design

Each PDF is written to `generated_certificates/<job_id>/<certificate_id>.pdf`. IDs are validated before use and the download handler resolves the path and verifies it remains below the configured root, preventing traversal. The predefined template includes organization, title, recipient, event, date, ID, and signatory area.

## Important Design Decisions

- FastAPI provides typed request contracts, OpenAPI, and a small dependency-injection surface.
- PostgreSQL provides durable relational job state and useful constraints.
- SQLAlchemy keeps persistence testable through injected sessions.
- BackgroundTasks returns quickly without introducing Redis/Celery complexity prematurely.
- Files are stored on the local volume while database rows store metadata; object storage is a natural next step for multiple API instances.

## Limitations and Future Improvements

FastAPI `BackgroundTasks` is process-local and is not a durable queue. A production scale-out would use Celery/RQ, Redis, object storage, retries with idempotency keys, authentication, rate limiting, and metrics/tracing. The current service is deliberately small enough to explain in an interview.
