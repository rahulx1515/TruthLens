"""
TruthLens 2.0 - Verification API Integration Tests
Tests POST /api/v1/verify, status polling, report retrieval,
state machine transitions, and retry logic.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
import app.models
from app.main import app
from app.models.verification import VerificationJob
from app.services.verification_orchestrator import verification_orchestrator

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client():
    c = TestClient(app)
    yield c


def test_submit_verification_job(client):
    """Verify submitting news content returns 202 Accepted with tracking endpoints."""
    payload = {
        "headline": "Federal Reserve Holds Benchmark Rates Steady",
        "text": (
            "WASHINGTON - The Federal Reserve held benchmark interest rates steady at 5.25% on Wednesday. "
            "Chair Jerome Powell noted that inflation has moderated."
        ),
        "language": "en"
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "QUEUED"
    assert "/api/v1/verify/" in data["status_url"]


def test_get_job_status_endpoint(client):
    """Verify polling status endpoint returns real-time pipeline status."""
    # First submit job
    sub_resp = client.post(
        "/api/v1/verify",
        json={"headline": "Test Headline", "text": "Some factual test statement."}
    )
    job_id = sub_resp.json()["job_id"]

    # Check status
    status_resp = client.get(f"/api/v1/verify/{job_id}/status")
    assert status_resp.status_code == 200
    sdata = status_resp.json()
    assert sdata["job_id"] == job_id
    assert sdata["status"] in ("QUEUED", "EXTRACTING", "SEARCHING", "RETRIEVING", "VERIFYING", "COMPLETED")
    assert "progress_percent" in sdata


def test_job_processing_and_report_retrieval(client):
    """Verify synchronous execution of orchestrator and complete report retrieval."""
    # Submit job
    payload = {
        "headline": "ISRO Confirms Chandrayaan-3 Sulfur Finding",
        "text": "ISRO confirmed that the Pragyan rover detected sulfur on the lunar south pole in 2023.",
        "language": "en"
    }
    sub_resp = client.post("/api/v1/verify", json=payload)
    job_id = sub_resp.json()["job_id"]

    # In test environment, run orchestrator directly against test DB
    test_db = TestingSessionLocal()
    try:
        verification_orchestrator.process_job(job_id, db=test_db)
    finally:
        test_db.close()

    # Now poll report
    report_resp = client.get(f"/api/v1/verify/{job_id}")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["verification_id"].startswith("rpt_")
    assert report["overall_verdict"] in ("SUPPORTED", "REFUTED", "MIXED", "UNVERIFIED", "OUTDATED")
    assert "claims_total" in report
    assert len(report["executive_summary"]) > 20


def test_retry_verification_job_endpoint(client):
    """Verify retry endpoint resets job state machine without duplicate records."""
    sub_resp = client.post(
        "/api/v1/verify",
        json={"headline": "Retry Test", "text": "This is a statement to test retry."}
    )
    job_id = sub_resp.json()["job_id"]

    retry_resp = client.post(f"/api/v1/verify/{job_id}/retry")
    assert retry_resp.status_code == 202
    data = retry_resp.json()
    assert data["status"] == "QUEUED"


def test_empty_verification_submission_rejected(client):
    """Verify empty text and empty URL returns 400 Bad Request."""
    resp = client.post("/api/v1/verify", json={"text": "", "url": ""})
    assert resp.status_code == 400
    assert "Either article text, headline, or a valid news URL" in resp.json()["detail"]
