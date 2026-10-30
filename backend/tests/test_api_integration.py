"""
TruthLens - Full Integration Tests
Tests Authentication, News Prediction, History, Authorization, and Dashboard Stats.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.session import Base, get_db
import app.models
from app.main import app

from sqlalchemy.pool import StaticPool

# Use isolated in-memory SQLite database for test suite with StaticPool
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


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_user_registration_and_login(client):
    # Register user A
    reg_payload = {
        "email": "user_a@truthlens.ai",
        "password": "Password123!",
        "full_name": "User Alpha"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "user_a@truthlens.ai"
    assert "password" not in user_data
    assert "hashed_password" not in user_data

    # Duplicate registration should be rejected
    dup_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@truthlens.ai", "password": "Password123!"}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Current user info
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "user_a@truthlens.ai"


def test_analyze_news_api(client):
    # Login user A
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@truthlens.ai", "password": "Password123!"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Analyze real article
    payload = {
        "title": "WASHINGTON (Reuters) - U.S. Congress passes budget resolution",
        "text": "WASHINGTON (Reuters) - Lawmakers concluded negotiations on Wednesday, approving the federal funding resolution.",
        "model_name": "logistic_regression"
    }
    resp = client.post("/api/v1/analyze", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction"] == "REAL"
    assert data["label"] == "Likely Authentic"
    assert data["confidence"] > 0.8
    assert data["model_name"] == "Logistic Regression"
    assert "explanation" in data
    assert "disclaimer" in data
    assert data["id"] is not None

    # Empty text validation failure
    empty_resp = client.post("/api/v1/analyze", json={"title": "", "text": ""}, headers=headers)
    assert empty_resp.status_code == 422


def test_analyses_history_and_authorization(client):
    # Register user B
    client.post(
        "/api/v1/auth/register",
        json={"email": "user_b@truthlens.ai", "password": "Password456!", "full_name": "User Beta"}
    )
    token_b = client.post(
        "/api/v1/auth/login",
        json={"email": "user_b@truthlens.ai", "password": "Password456!"}
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Login user A
    token_a = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@truthlens.ai", "password": "Password123!"}
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A creates an analysis
    payload = {
        "title": "Confidential Report on Global Economy",
        "text": "Analysts suggest sustained growth across markets in the coming fiscal quarter."
    }
    create_resp = client.post("/api/v1/analyze", json=payload, headers=headers_a)
    analysis_id = create_resp.json()["id"]

    # User A can view it
    get_resp_a = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers_a)
    assert get_resp_a.status_code == 200
    assert get_resp_a.json()["id"] == analysis_id

    # User B CANNOT access User A's analysis (403 Forbidden)
    get_resp_b = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers_b)
    assert get_resp_b.status_code == 403

    # User B CANNOT delete User A's analysis (403 Forbidden)
    del_resp_b = client.delete(f"/api/v1/analyses/{analysis_id}", headers=headers_b)
    assert del_resp_b.status_code == 403

    # User A CAN delete their own analysis
    del_resp_a = client.delete(f"/api/v1/analyses/{analysis_id}", headers=headers_a)
    assert del_resp_a.status_code == 204


def test_dashboard_stats_api(client):
    token_a = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@truthlens.ai", "password": "Password123!"}
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    stats_resp = client.get("/api/v1/dashboard/stats", headers=headers_a)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_analyses" in stats
    assert "fake_count" in stats
    assert "authentic_count" in stats
    assert "fake_percentage" in stats
    assert "authentic_percentage" in stats
    assert "recent_analyses" in stats
    assert "daily_trend" in stats


def test_models_performance_api(client):
    perf_resp = client.get("/api/v1/models/performance")
    assert perf_resp.status_code == 200
    perf = perf_resp.json()
    assert perf["selected_production_model"] == "Logistic Regression"
    assert "models" in perf
    assert len(perf["models"]) >= 2
    # Check Logistic Regression metrics are validated
    lr = next(m for m in perf["models"] if "logistic" in m["key"].lower())
    assert lr["accuracy"] > 95.0
    assert lr["f1_score"] > 95.0
    assert lr["confusion_matrix"] is not None


def test_url_extractor_ssrf_rejection(client):
    token_a = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@truthlens.ai", "password": "Password123!"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token_a}"}

    # Attempting to scan internal loopback or private ranges must fail with 400
    bad_payload = {
        "url": "http://127.0.0.1:8000/internal-admin",
        "title": "",
        "text": ""
    }
    resp = client.post("/api/v1/analyze", json=bad_payload, headers=headers)
    assert resp.status_code == 400
    assert "Extraction Failed" in resp.json()["detail"]
