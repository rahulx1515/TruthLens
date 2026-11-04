"""
TruthLens - Tests for Render Blueprint Specification (render.yaml)
Validates:
- Blueprint schema valid YAML
- Backend web service properly configured
- Frontend static site properly configured with SPA client rewrite
- No 'databases:' block present (preventing duplicate database creation)
- DATABASE_URL configured with sync: false to connect existing 'truthlens-db'
- VITE_API_URL configured from backend service host
- Secret key generated securely
"""
import os
import yaml
import pytest


@pytest.fixture
def render_config():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    render_yaml_path = os.path.join(root_dir, "render.yaml")
    assert os.path.exists(render_yaml_path), f"render.yaml not found at {render_yaml_path}"
    with open(render_yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_no_databases_block_defined(render_config):
    """
    CRITICAL: Verify that NO 'databases:' section exists in render.yaml.
    Render automatically tries to provision a new managed database if 'databases:'
    is declared. The user has an existing database 'truthlens-db'.
    """
    assert "databases" not in render_config, (
        "Duplicate database risk: 'databases:' must not be defined in render.yaml "
        "when connecting to an existing Render database."
    )


def test_backend_service_configuration(render_config):
    """Validate backend web service definitions."""
    services = render_config.get("services", [])
    backend = next((s for s in services if s.get("name") == "truthlens-backend"), None)
    assert backend is not None, "truthlens-backend service not found in render.yaml"
    assert backend.get("type") == "web"
    assert backend.get("runtime") == "python"
    assert "alembic upgrade head" in backend.get("buildCommand", "")
    assert backend.get("healthCheckPath") == "/health"

    # Verify envVars
    env_vars = {item["key"]: item for item in backend.get("envVars", [])}
    assert "DATABASE_URL" in env_vars
    # DATABASE_URL must have sync: false
    assert env_vars["DATABASE_URL"].get("sync") is False, (
        "DATABASE_URL must have sync: false to connect existing truthlens-db"
    )

    assert "SECRET_KEY" in env_vars
    assert env_vars["SECRET_KEY"].get("generateValue") is True

    assert "ENABLE_LOCAL_NEURAL_NLI" in env_vars
    assert str(env_vars["ENABLE_LOCAL_NEURAL_NLI"].get("value")).lower() == "false"


def test_frontend_service_configuration(render_config):
    """Validate frontend static site definitions."""
    services = render_config.get("services", [])
    frontend = next((s for s in services if s.get("name") == "truthlens-frontend"), None)
    assert frontend is not None, "truthlens-frontend service not found in render.yaml"
    assert frontend.get("type") == "web"
    assert frontend.get("runtime") == "static"
    assert frontend.get("staticPublishPath") == "dist"

    # SPA rewrite rule
    routes = frontend.get("routes", [])
    assert any(
        r.get("type") == "rewrite" and r.get("source") == "/*" and r.get("destination") == "/index.html"
        for r in routes
    ), "Missing SPA client-side routing rewrite rule (/* -> /index.html)"

    # VITE_API_URL wired from backend service host
    env_vars = {item["key"]: item for item in frontend.get("envVars", [])}
    assert "VITE_API_URL" in env_vars
    from_service = env_vars["VITE_API_URL"].get("fromService", {})
    assert from_service.get("name") == "truthlens-backend"
    assert from_service.get("envVarKey") == "RENDER_EXTERNAL_URL"

