import os
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.main import app


def test_cors_local_dev_origin_accepted():
    """Verify standard local Vite development origin is accepted with credentials."""
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_production_vercel_origin_accepted():
    """Verify production Vercel frontend origin is accepted with credentials."""
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://fakedeal-buster.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://fakedeal-buster.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_local_ip_origin_accepted():
    """Verify 127.0.0.1 loopback origin is accepted with credentials."""
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_unauthorized_vercel_origin_rejected_by_default():
    """
    Verify that arbitrary Vercel origins are rejected by default.
    Prevents unauthorized third-party Vercel subdomains from making credentialed requests.
    """
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://malicious-phishing-site.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    # When CORS rejects an origin, Access-Control-Allow-Origin header is omitted
    assert "access-control-allow-origin" not in response.headers


def test_cors_arbitrary_external_origin_rejected():
    """Verify arbitrary third-party domain is rejected."""
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil-attacker.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_dynamically_configured_production_origin():
    """
    Verify that configuring a specific production origin (e.g., via CORS_ALLOWED_ORIGINS)
    permits that exact domain while still rejecting unauthorized domains.
    """
    test_app = FastAPI()
    allowed = ["http://localhost:5173", "https://authorized-client.vercel.app"]
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(test_app)

    # Authorized production origin
    res_auth = client.options(
        "/ping",
        headers={
            "Origin": "https://authorized-client.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_auth.status_code == 200
    assert res_auth.headers.get("access-control-allow-origin") == "https://authorized-client.vercel.app"
    assert res_auth.headers.get("access-control-allow-credentials") == "true"

    # Unauthorized Vercel origin
    res_unauth = client.options(
        "/ping",
        headers={
            "Origin": "https://different-unauthorized.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in res_unauth.headers


def test_cors_narrow_scoped_origin_regex():
    """
    Verify that when an operator explicitly provides a scoped regex (e.g. for preview branches),
    only matching project domains are allowed and others are rejected.
    """
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_origin_regex=r"^https://fakedeal-buster(-[a-z0-9-]+)?\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(test_app)

    # Valid preview origin matching the pattern
    res_preview = client.options(
        "/ping",
        headers={
            "Origin": "https://fakedeal-buster-preview-12.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_preview.status_code == 200
    assert res_preview.headers.get("access-control-allow-origin") == "https://fakedeal-buster-preview-12.vercel.app"
    assert res_preview.headers.get("access-control-allow-credentials") == "true"

    # Unrelated Vercel project not matching the pattern
    res_other = client.options(
        "/ping",
        headers={
            "Origin": "https://another-project.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in res_other.headers
