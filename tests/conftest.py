import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_certificates.db"
os.environ["GENERATED_CERTIFICATES_DIR"] = "test_generated_certificates"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.api.routes import jobs as jobs_routes

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(engine)
jobs_routes.SessionLocal = TestingSessionLocal


def override_get_db():
    with TestingSessionLocal() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database():
    yield
    with TestingSessionLocal() as db:
        db.execute(text("DELETE FROM certificates"))
        db.execute(text("DELETE FROM generation_jobs"))
        db.commit()
    output = Path("test_generated_certificates")
    if output.exists():
        for path in sorted(output.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()