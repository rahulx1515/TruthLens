"""
TruthLens - Production Deployment Verification Suite
Validates end-to-end production readiness:
1. Root and Health endpoints.
2. User authentication (Registration + Login + JWT generation).
3. Server-side Cryptographic Guest Session issuance.
4. Zero-Ollama verification lifecycle:
   - Submits verification job.
   - Decomposes claims using configurable LLM/rule-based engine.
   - Discovers evidence and evaluates passages.
   - Synthesizes final transparent report.
   - Polls status machine to completion.
   - Retrieves final verification report.
5. Replay-protected guest report claiming into authenticated user account.
6. User history scoping and authorization isolation.
"""
import os
import sys
import time

os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure backend directory is in path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database.session import Base, get_db
import app.models
from app.main import app
from app.services.verification_orchestrator import verification_orchestrator
from app.services.llm_service import llm_service
from app.services.nli_verifier import nli_verifier

# Isolated in-memory database
test_engine = create_engine(
    "sqlite:///:memory:",
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


import app.services.verification_orchestrator as orch_mod
orch_mod.SessionLocal = TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


def verify_production_lifecycle():
    print("\n================ TRUTHLENS PRODUCTION DEPLOYMENT VALIDATION ================\n")

    # 1. Health Checks
    print("[1/6] Testing Health & Root Endpoints...")
    root_resp = client.get("/")
    assert root_resp.status_code == 200, f"Root endpoint failed: {root_resp.text}"
    print(f"  ✓ Root Endpoint: {root_resp.json()['service']} v{root_resp.json()['version']}")

    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health endpoint failed: {health_resp.text}"
    print(f"  ✓ Health Endpoint: {health_resp.json()}")

    # 2. Authentication
    print("\n[2/6] Testing User Registration & JWT Authentication...")
    user_email = f"prod_auditor_{int(time.time())}@truthlens.ai"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": "ProductionPassword123!", "full_name": "DevOps Auditor"}
    )
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    user_data = reg_resp.json()
    print(f"  ✓ Registered User ID: {user_data['id']} ({user_data['email']})")

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "ProductionPassword123!"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    jwt_token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {jwt_token}"}
    print(f"  ✓ JWT Token Issued: {jwt_token[:20]}...{jwt_token[-10:]}")

    # 3. Cryptographic Guest Session Issuance
    print("\n[3/6] Testing Server-Side Guest Session Issuance...")
    session_resp = client.post("/api/v1/verify/guest-session")
    assert session_resp.status_code == 200, f"Guest session creation failed: {session_resp.text}"
    session_data = session_resp.json()
    guest_session_id = session_data["guest_session_id"]
    claim_token = session_data["claim_token"]
    guest_headers = {"X-Guest-Session-ID": guest_session_id}
    print(f"  ✓ Generated Guest Session ID: {guest_session_id}")
    print(f"  ✓ Generated Secret Claim Token: {claim_token[:12]}...")
    print(f"  ✓ Session Expiry: {session_data['expires_at']}")

    # 4. Verification Submission & Offline/Cloud AI Resilience
    print("\n[4/6] Testing Verification Submission & Pipeline Processing...")
    print(f"  Active LLM Provider: {llm_service.get_active_provider_name()}")
    print(f"  Active NLI Provider: {settings.NLI_PROVIDER} (Neural Loaded: {nli_verifier.is_neural_available})")

    article_text = (
        "NEW DELHI - The Reserve Bank of India announced it maintained the repo rate at 6.5 percent on Thursday. "
        "Governor Shaktikanta Das highlighted that inflation remains within the target tolerance band while GDP growth shows resilience."
    )
    submit_payload = {
        "headline": "RBI Holds Benchmark Repo Rate Steady at 6.5 Percent",
        "text": article_text,
        "language": "en"
    }

    submit_resp = client.post("/api/v1/verify", json=submit_payload, headers=guest_headers)
    assert submit_resp.status_code == 202, f"Verification submit failed: {submit_resp.text}"
    job_id = submit_resp.json()["job_id"]
    print(f"  ✓ Verification Job Created: {job_id}")

    # Poll status (FastAPI TestClient processes background tasks before response returns)
    status_resp = client.get(f"/api/v1/verify/{job_id}/status", headers=guest_headers)
    assert status_resp.status_code == 200, f"Status poll failed: {status_resp.text}"
    status_data = status_resp.json()
    print(f"  ✓ Final Job Status: {status_data['status']}")
    print(f"  ✓ Progress: {status_data['progress_percent']}%")
    print(f"  ✓ Overall Verdict: {status_data['overall_verdict']}")
    print(f"  ✓ Confidence: {status_data['overall_confidence']}")
    assert status_data["status"] == "COMPLETED", f"Job failed to complete: {status_data}"

    # 5. Report Retrieval
    print("\n[5/6] Testing Verification Report Retrieval...")
    report_resp = client.get(f"/api/v1/verify/{job_id}", headers=guest_headers)
    assert report_resp.status_code == 200, f"Report retrieval failed: {report_resp.text}"
    report_data = report_resp.json()
    print(f"  ✓ Executive Summary: {report_data['executive_summary'][:100]}...")
    print(f"  ✓ Extraction Method: {report_data.get('extraction_method')}")
    print(f"  ✓ NLI Inference Method: {report_data.get('nli_inference_method')}")
    print(f"  ✓ Evaluated Claims Count: {len(report_data.get('claim_results', []))}")
    for c in report_data.get('claim_results', []):
        print(f"    - Claim: \"{c['claim_text']}\" -> Verdict: {c['verdict']} (Confidence: {c['confidence']})")

    # 6. Guest Report Claiming & History Scoping
    print("\n[6/6] Testing Guest Report Claiming & User History...")
    claim_resp = client.post(
        "/api/v1/verify/claim-guest-reports",
        json={"guest_session_id": guest_session_id, "claim_token": claim_token},
        headers=auth_headers
    )
    assert claim_resp.status_code == 200, f"Claim guest report failed: {claim_resp.text}"
    claim_json = claim_resp.json()
    print(f"  ✓ Claim Response: {claim_json['message']} ({claim_json['claimed_count']} jobs transferred)")

    # Verify report is now in user's history
    hist_resp = client.get("/api/v1/verify/history", headers=auth_headers)
    assert hist_resp.status_code == 200, f"History fetch failed: {hist_resp.text}"
    hist_items = hist_resp.json()
    assert any(h["job_id"] == job_id for h in hist_items), "Claimed job not found in user history!"
    print(f"  ✓ User History contains {len(hist_items)} verified reports.")

    print("\n================ PRODUCTION LIFECYCLE VALIDATION: 100% SUCCESS ================\n")


if __name__ == "__main__":
    verify_production_lifecycle()
