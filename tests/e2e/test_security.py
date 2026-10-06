def test_security_headers(make_client):
    r = make_client().get("/api/v1/pets")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert "x-powered-by" not in r.headers
    assert r.headers["RateLimit-Limit"]
    assert r.headers["RateLimit-Remaining"]
    assert "X-RateLimit-Limit" not in r.headers


def test_cors_only_allows_frontend_origin(make_client):
    c = make_client()
    allowed = c.options(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    denied = c.options(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in denied.headers


def test_json_body_limit(make_client):
    r = make_client().post(
        "/api/v1/auth/login",
        content=b'{"email": "' + b"a" * 200_000 + b'"}',
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413
    assert r.json()["success"] is False


def test_unknown_route_uses_standard_error_format(make_client):
    r = make_client().get("/api/v1/does-not-exist")
    assert r.status_code == 404
    assert r.json() == {"success": False, "message": "Recurso no encontrado", "errors": []}


def test_uploaded_images_are_served_without_script_execution(admin_client, make_client):
    from tests.helpers import make_png

    r = admin_client.post(
        "/api/v1/admin/products",
        data={"name": "Collar"},
        files={"image": ("c.png", make_png(), "image/png")},
    )
    path = r.json()["data"]["image_url"].removeprefix("http://testserver")
    image = make_client().get(path)
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/webp"
    assert "sandbox" in image.headers["Content-Security-Policy"]
    assert make_client().get("/uploads/images/../../core/config/settings.py").status_code == 404
