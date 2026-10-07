# Interview Notes

1. **Why FastAPI?** Typed validation, automatic OpenAPI documentation, dependency injection, and a small clear routing layer.
2. **Why PostgreSQL?** Durable relational state, foreign keys, indexes, and transactions fit jobs and certificate records.
3. **Why SQLAlchemy?** It separates persistence from services and makes test-session injection straightforward.
4. **Why background processing?** PDF generation can be slow; returning 202 quickly keeps the API responsive.
5. **Why not synchronous processing?** A request should not stay open for a large bulk job or time out while rendering PDFs.
6. **How does bulk processing work?** One request creates one job and pending rows; the worker loops through recipients independently.
7. **How is progress calculated?** `(successful + failed) / total * 100`, clamped to 100, with pending derived from the remaining count.
8. **How are failures isolated?** Each recipient has its own try/except and database commit. One exception records a failed certificate and the loop continues.
9. **How are certificates stored?** PDFs are under `generated_certificates/<job_id>/`; rows store status, metadata, and the generated path.
10. **How is traversal prevented?** Recipient IDs allow only safe characters; download paths are resolved and checked to remain below the configured root.
11. **How would you scale to 100,000 certificates?** Use a durable queue, multiple workers, object storage, chunked submission, database counters, and rate limits.
12. **How would you introduce Redis/Celery?** Publish a job ID to a queue, have workers claim recipient batches, and update the same database state.
13. **How would you make jobs retryable?** Add attempt counts and retry timestamps per certificate, then retry only transient failures with backoff.
14. **How would you handle duplicate requests?** Accept an idempotency key and enforce a unique constraint for the organization/request combination.
15. **How would you make generation idempotent?** Use a deterministic job/request key and skip completed certificate IDs during retries.
16. **How would you monitor jobs?** Emit structured logs, metrics for duration/failure rate, queue depth, and traces around generation and storage.
17. **What are the current limitations?** BackgroundTasks is process-local, local files are not shared storage, and authentication is intentionally outside the assignment.
