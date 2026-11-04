import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_bootstrap_returns_only_public_metadata() -> None:
    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    assert response.json() == {"name": "Manpower ERP", "stage": "bootstrap"}


@pytest.mark.parametrize("company", ["company-a", "company-b"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_business_routes_are_not_available(company: str, method: str) -> None:
    response = client.request(
        method,
        f"/api/companies/{company}/invoices",
        headers={"X-Company-ID": company, "X-Role": "admin"},
    )
    assert response.status_code == 404


def test_bootstrap_is_read_only() -> None:
    assert (
        client.post("/api/bootstrap", json={"stage": "production"}).status_code == 405
    )


def test_openapi_declares_bootstrap_contract() -> None:
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/api/bootstrap",
        "/api/health/live",
        "/api/health/ready",
        "/api/auth/login",
        "/api/auth/me",
        "/api/auth/logout",
        "/api/auth/password",
    }
    assert "Bootstrap" in schema["components"]["schemas"]
    for status in ("422", "503"):
        response_schema = schema["paths"]["/api/health/ready"]["get"]["responses"][
            status
        ]
        assert response_schema["content"]["application/json"]["schema"]["$ref"] == (
            "#/components/schemas/ErrorResponse"
        )
