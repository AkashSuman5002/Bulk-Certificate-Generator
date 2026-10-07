from tests.test_jobs import payload


def create_job(client, count=2):
    response = client.post("/api/v1/jobs", json=payload(count))
    assert response.status_code == 202
    return response.json()


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_valid_job_creation(client):
    result = create_job(client, 2)
    assert result["status"] == "pending"
    assert result["total"] == 2


def test_empty_recipient_list(client):
    data = payload()
    data["recipients"] = []
    assert client.post("/api/v1/jobs", json=data).status_code == 422


def test_invalid_email(client):
    data = payload()
    data["recipients"][0]["email"] = "wrong-email"
    assert client.post("/api/v1/jobs", json=data).status_code == 422


def test_missing_required_field(client):
    data = payload()
    del data["organization_name"]
    assert client.post("/api/v1/jobs", json=data).status_code == 422


def test_duplicate_certificate_ids(client):
    data = payload()
    data["recipients"][1]["certificate_id"] = data["recipients"][0]["certificate_id"]
    assert client.post("/api/v1/jobs", json=data).status_code == 422


def test_multiple_recipients(client):
    job_id = create_job(client, 5)["job_id"]
    listing = client.get(f"/api/v1/jobs/{job_id}/certificates").json()
    assert listing["total"] == 5
    assert len(listing["items"]) == 5


def test_certificate_generation(client):
    job_id = create_job(client, 1)["job_id"]
    item = client.get(f"/api/v1/jobs/{job_id}/certificates").json()["items"][0]
    download = client.get(item["download_url"])
    assert item["status"] == "completed"
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")


def test_job_status_and_progress(client):
    job_id = create_job(client, 2)["job_id"]
    status = client.get(f"/api/v1/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert status.json()["successful"] == 2
    assert status.json()["failed"] == 0
    assert status.json()["pending"] == 0
    assert status.json()["progress_percentage"] == 100


def test_successful_completion(client):
    job_id = create_job(client, 3)["job_id"]
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "completed"


def test_individual_certificate_failure(client, monkeypatch):
    from app.services import certificate_service

    original = certificate_service.generate_certificate

    def fail_one(job, certificate_id, recipient_name):
        if certificate_id == "CERT-002":
            raise OSError("simulated PDF failure")
        return original(job, certificate_id, recipient_name)

    monkeypatch.setattr(certificate_service, "generate_certificate", fail_one)
    job_id = create_job(client, 3)["job_id"]
    items = client.get(f"/api/v1/jobs/{job_id}/certificates").json()["items"]
    failed = next(item for item in items if item["certificate_id"] == "CERT-002")
    assert failed["status"] == "failed"
    assert "simulated PDF failure" in failed["error_message"]
    assert client.get(f"/api/v1/certificates/{'00000000-0000-0000-0000-000000000000'}/download").status_code == 404


def test_failure_isolation_and_completed_with_errors(client, monkeypatch):
    from app.services import certificate_service

    original = certificate_service.generate_certificate

    def fail_third(job, certificate_id, recipient_name):
        if certificate_id == "CERT-002":
            raise OSError("simulated third-recipient failure")
        return original(job, certificate_id, recipient_name)

    monkeypatch.setattr(certificate_service, "generate_certificate", fail_third)
    job_id = create_job(client, 5)["job_id"]
    status = client.get(f"/api/v1/jobs/{job_id}").json()
    assert status["status"] == "completed_with_errors"
    assert status["total"] == 5
    assert status["successful"] == 4
    assert status["failed"] == 1
    items = client.get(f"/api/v1/jobs/{job_id}/certificates").json()["items"]
    statuses = {item["certificate_id"]: item["status"] for item in items}
    assert statuses == {
        "CERT-000": "completed",
        "CERT-001": "completed",
        "CERT-002": "failed",
        "CERT-003": "completed",
        "CERT-004": "completed",
    }


def test_certificate_listing_and_pagination(client):
    job_id = create_job(client, 5)["job_id"]
    page = client.get(f"/api/v1/jobs/{job_id}/certificates?page=2&page_size=2")
    assert page.status_code == 200
    assert page.json()["total"] == 5
    assert len(page.json()["items"]) == 2


def test_nonexistent_job_returns_404(client):
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_NOT_FOUND"


def test_nonexistent_certificate_returns_404(client):
    response = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CERTIFICATE_NOT_FOUND"