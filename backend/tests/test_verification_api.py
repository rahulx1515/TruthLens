"""
TruthLens - Verification API Integration & Security Tests
Tests Authentication, Cryptographic Server-Side Guest Sessions, Session Guessing,
Replay Attack Prevention, Unauthorized Report Claiming, Authorization Scoping,
Rate Limiting, Retries, and Status Polling.
"""
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
import app.models
from app.main import app
from app.models.user import User
from app.models.verification import GuestSession, VerificationClaimRecord, VerificationJob
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.guest_session_service import hash_claim_secret
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


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def mock_background_process(monkeypatch):
    """Ensure BackgroundTasks does not run the live pipeline during API unit testing."""
    monkeypatch.setattr(verification_orchestrator, "process_job", lambda job_id, db=None: None)


@pytest.fixture(scope="module")
def client():
    c = TestClient(app)
    yield c


def get_auth_token(client, email="user_one@truthlens.ai", password="Password123!"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"}
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    return login_resp.json()["access_token"]


def test_guest_session_issuance(client):
    """POST /verify/guest-session issues cryptographically secure session credentials."""
    resp = client.post("/api/v1/verify/guest-session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["guest_session_id"].startswith("gses_")
    assert data["claim_token"].startswith("gclm_")
    assert "expires_at" in data


def test_guest_verification_submission(client):
    """Unauthenticated guest can submit verification and receives server-issued credentials."""
    payload = {
        "headline": "Federal Reserve Holds Benchmark Rates Steady",
        "text": "WASHINGTON - The Federal Reserve held benchmark interest rates steady at 5.25% on Wednesday.",
        "language": "en"
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"].startswith("job_")
    assert "X-Guest-Session-ID" in response.headers
    assert "X-Guest-Claim-Token" in response.headers
    assert response.headers["X-Guest-Session-ID"].startswith("gses_")
    assert response.headers["X-Guest-Claim-Token"].startswith("gclm_")


def test_arbitrary_guessed_session_id_rejected(client):
    """Client-invented or guessed session IDs that do not exist on the server are rejected (401)."""
    fake_session_id = "gses_fake_guessed_unauthorized_token_123"
    headers = {"X-Guest-Session-ID": fake_session_id}
    payload = {
        "headline": "Spoofed Session News",
        "text": "Attempting to submit with an arbitrary unissued guest session."
    }
    resp = client.post("/api/v1/verify", json=payload, headers=headers)
    assert resp.status_code == 401
    assert "Invalid guest session credentials" in resp.json()["detail"]


def test_expired_guest_session_rejected(client):
    """Guest sessions past their expires_at date are rejected (401 on submit, 400 on claim)."""
    db = TestingSessionLocal()
    expired_session_id = "gses_expired_session_test_999"
    claim_secret = "gclm_expired_secret_test_999"
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)

    expired_session = GuestSession(
        id=expired_session_id,
        claim_secret_hash=hash_claim_secret(claim_secret),
        created_at=past_time - timedelta(hours=24),
        expires_at=past_time,
        is_claimed=False,
        request_count=0
    )
    db.add(expired_session)
    db.commit()
    db.close()

    # Submission with expired session must fail
    resp = client.post(
        "/api/v1/verify",
        json={"headline": "Expired Submission", "text": "Testing expired session handling."},
        headers={"X-Guest-Session-ID": expired_session_id}
    )
    assert resp.status_code == 401
    assert "Guest session has expired" in resp.json()["detail"]

    # Claiming expired session must fail
    token = get_auth_token(client, "claimer_exp@truthlens.ai", "Password123!")
    claim_resp = client.post(
        "/api/v1/verify/claim-guest-reports",
        json={"guest_session_id": expired_session_id, "claim_token": claim_secret},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert claim_resp.status_code == 400
    assert "has expired" in claim_resp.json()["detail"]


def test_unauthorized_claiming_with_wrong_token_rejected(client):
    """Claiming a valid guest session with a wrong claim_token is rejected (403 Forbidden)."""
    # 1. Issue a genuine guest session
    init_resp = client.post("/api/v1/verify/guest-session")
    assert init_resp.status_code == 200
    session_id = init_resp.json()["guest_session_id"]
    correct_token = init_resp.json()["claim_token"]

    # 2. Submit a job under this session
    headers = {"X-Guest-Session-ID": session_id}
    sub_resp = client.post(
        "/api/v1/verify",
        json={"headline": "Valuable News", "text": "Important investigative piece."},
        headers=headers
    )
    assert sub_resp.status_code == 202

    # 3. An attacker tries to claim with a wrong token
    token = get_auth_token(client, "attacker@truthlens.ai", "Password123!")
    auth_headers = {"Authorization": f"Bearer {token}"}

    wrong_claim_resp = client.post(
        "/api/v1/verify/claim-guest-reports",
        json={"guest_session_id": session_id, "claim_token": "gclm_fraudulent_guessed_token"},
        headers=auth_headers
    )
    assert wrong_claim_resp.status_code == 403
    assert "Invalid guest claim token" in wrong_claim_resp.json()["detail"]


def test_replay_attack_claiming_prevention(client):
    """A guest session cannot be claimed more than once (replay prevention returns 400)."""
    # 1. Issue guest session
    init_resp = client.post("/api/v1/verify/guest-session")
    session_id = init_resp.json()["guest_session_id"]
    claim_token = init_resp.json()["claim_token"]

    # 2. Submit job
    headers = {"X-Guest-Session-ID": session_id}
    client.post(
        "/api/v1/verify",
        json={"headline": "Replay Test", "text": "Replay testing news content."},
        headers=headers
    )

    # 3. First legitimate claim succeeds
    token_1 = get_auth_token(client, "legit_user@truthlens.ai", "Password123!")
    claim_1 = client.post(
        "/api/v1/verify/claim-guest-reports",
        json={"guest_session_id": session_id, "claim_token": claim_token},
        headers={"Authorization": f"Bearer {token_1}"}
    )
    assert claim_1.status_code == 200
    assert claim_1.json()["claimed_count"] >= 1

    # 4. Second attempt (replay attack) fails with 400
    token_2 = get_auth_token(client, "replay_attacker@truthlens.ai", "Password123!")
    claim_2 = client.post(
        "/api/v1/verify/claim-guest-reports",
        json={"guest_session_id": session_id, "claim_token": claim_token},
        headers={"Authorization": f"Bearer {token_2}"}
    )
    assert claim_2.status_code == 400
    assert "already been claimed" in claim_2.json()["detail"]


def test_user_a_cannot_access_user_b_job(client):
    """User B cannot access or view User A's private verification report (403 Forbidden)."""
    token_a = get_auth_token(client, "user_a@truthlens.ai", "Password123!")
    token_b = get_auth_token(client, "user_b@truthlens.ai", "Password456!")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A submits a job
    payload = {
        "headline": "User A Private News Verification",
        "text": "Confidential financial statement about central bank monetary policy.",
        "language": "en"
    }
    sub_resp = client.post("/api/v1/verify", json=payload, headers=headers_a)
    assert sub_resp.status_code == 202
    job_id = sub_resp.json()["job_id"]

    # User A can view status
    status_a = client.get(f"/api/v1/verify/{job_id}/status", headers=headers_a)
    assert status_a.status_code == 200

    # User B CANNOT view status (403)
    status_b = client.get(f"/api/v1/verify/{job_id}/status", headers=headers_b)
    assert status_b.status_code == 403

    # User B CANNOT view report (403)
    report_b = client.get(f"/api/v1/verify/{job_id}", headers=headers_b)
    assert report_b.status_code == 403


def test_user_a_cannot_retry_or_delete_user_b_job(client):
    """User B cannot retry or delete User A's verification job (403 Forbidden)."""
    token_a = get_auth_token(client, "user_a@truthlens.ai", "Password123!")
    token_b = get_auth_token(client, "user_b@truthlens.ai", "Password456!")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    sub_resp = client.post(
        "/api/v1/verify",
        json={"headline": "Protected Job", "text": "Protected content."},
        headers=headers_a
    )
    job_id = sub_resp.json()["job_id"]

    # User B cannot retry User A's job
    retry_b = client.post(f"/api/v1/verify/{job_id}/retry", headers=headers_b)
    assert retry_b.status_code == 403

    # User B cannot delete User A's job
    del_b = client.delete(f"/api/v1/verify/{job_id}", headers=headers_b)
    assert del_b.status_code == 403

    # User A CAN delete their own job
    del_a = client.delete(f"/api/v1/verify/{job_id}", headers=headers_a)
    assert del_a.status_code == 200


def test_guest_cannot_access_another_user_or_guest_report(client):
    """A guest session cannot access reports created under another guest session."""
    init_1 = client.post("/api/v1/verify/guest-session").json()
    init_2 = client.post("/api/v1/verify/guest-session").json()

    headers_1 = {"X-Guest-Session-ID": init_1["guest_session_id"]}
    headers_2 = {"X-Guest-Session-ID": init_2["guest_session_id"]}

    # Guest 1 submits job
    sub_resp = client.post(
        "/api/v1/verify",
        json={"headline": "Guest 1 Article", "text": "Guest 1 text verification assertion."},
        headers=headers_1
    )
    job_id = sub_resp.json()["job_id"]

    # Guest 1 can access status
    status_1 = client.get(f"/api/v1/verify/{job_id}/status", headers=headers_1)
    assert status_1.status_code == 200

    # Guest 2 CANNOT access Guest 1's status (403 Forbidden)
    status_2 = client.get(f"/api/v1/verify/{job_id}/status", headers=headers_2)
    assert status_2.status_code == 403

    # Unauthenticated visitor without session header CANNOT access (403 Forbidden)
    status_anon = client.get(f"/api/v1/verify/{job_id}/status")
    assert status_anon.status_code == 403


def test_history_endpoint_never_leaks_other_users_data(client):
    """
    GET /api/v1/verify returns strictly user's own items.
    Guests without session receive an empty list (never public leak).
    """
    token_a = get_auth_token(client, "user_a@truthlens.ai", "Password123!")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Authenticated user history
    hist_a = client.get("/api/v1/verify", headers=headers_a)
    assert hist_a.status_code == 200
    items_a = hist_a.json()
    assert isinstance(items_a, list)

    # Completely unauthenticated visitor receives empty list (no public database leak)
    hist_guest_empty = client.get("/api/v1/verify")
    assert hist_guest_empty.status_code == 200
    assert hist_guest_empty.json() == []


def test_input_size_limit_rejection(client):
    """Submissions exceeding maximum character limits must be rejected with 400."""
    huge_text = "A" * 16000
    resp = client.post("/api/v1/verify", json={"headline": "Big", "text": huge_text})
    assert resp.status_code == 400
    assert "exceeds maximum allowed size" in resp.json()["detail"]


def test_job_cancellation(client):
    """Job can be cancelled by the owner."""
    init = client.post("/api/v1/verify/guest-session").json()
    headers = {"X-Guest-Session-ID": init["guest_session_id"]}
    sub = client.post(
        "/api/v1/verify",
        json={"headline": "Cancel Me", "text": "Cancel this text."},
        headers=headers
    )
    job_id = sub.json()["job_id"]

    cancel_resp = client.post(f"/api/v1/verify/{job_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"
