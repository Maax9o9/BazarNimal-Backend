import uuid

from tests.helpers import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


def _new_user() -> dict:
    return {
        "name": "Ana Pérez",
        "email": f"ana-{uuid.uuid4().hex[:8]}@bazarnimal-test.com",
        "phone": "55 1234 5678",
        "password": "Calavera#2026",
    }


def test_register_returns_user_without_sensitive_fields(make_client):
    c = make_client()
    r = c.post(REGISTER, json=_new_user())
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["role"] == "user"
    assert body["data"]["phone"] == "5512345678"
    assert "password_hash" not in body["data"]


def test_register_rejects_duplicate_email(make_client):
    c = make_client()
    data = _new_user()
    assert c.post(REGISTER, json=data).status_code == 201
    r = c.post(REGISTER, json={**data, "email": data["email"].upper()})
    assert r.status_code == 409


def test_register_rejects_mass_assignment_of_role(make_client):
    r = make_client().post(REGISTER, json={**_new_user(), "role": "admin"})
    assert r.status_code == 422
    assert {"field": "role", "message": "Campo no permitido"} in r.json()["errors"]


def test_register_enforces_password_policy(make_client):
    r = make_client().post(REGISTER, json={**_new_user(), "password": "password"})
    assert r.status_code == 422
    body = r.json()
    assert body == {
        "success": False,
        "message": "Datos inválidos",
        "errors": [
            {"field": "password", "message": "La contraseña debe tener una mayúscula, un número, un símbolo"}
        ],
    }


def test_login_sets_httponly_cookies_and_user_ttl(make_client):
    c = make_client()
    data = _new_user()
    c.post(REGISTER, json=data)
    r = c.post(LOGIN, json={"email": data["email"], "password": data["password"]})
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "user"
    assert r.json()["data"]["expires_in"] == 15 * 60
    cookies = r.headers.get_list("set-cookie")
    access = next(c for c in cookies if c.startswith("access_token="))
    refresh = next(c for c in cookies if c.startswith("refresh_token="))
    assert "HttpOnly" in access and "SameSite=strict" in access and "Max-Age=900" in access
    assert "HttpOnly" in refresh and "Path=/api/v1/auth" in refresh
    assert "access_token" not in r.text  # el token nunca va en el body


def test_admin_login_has_two_hour_ttl(make_client):
    r = make_client().post(LOGIN, json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD})
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "admin"
    assert r.json()["data"]["expires_in"] == 2 * 60 * 60


def test_login_error_is_generic(make_client):
    c = make_client()
    data = _new_user()
    c.post(REGISTER, json=data)
    wrong_password = c.post(LOGIN, json={"email": data["email"], "password": "Otra#Clave1"})
    unknown_email = c.post(LOGIN, json={"email": "nadie@bazarnimal-test.com", "password": "Otra#Clave1"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["message"] == unknown_email.json()["message"] == "Credenciales inválidas"


def test_account_locks_after_failed_attempts(make_client):
    c = make_client()
    data = _new_user()
    c.post(REGISTER, json=data)
    for _ in range(5):
        assert c.post(LOGIN, json={"email": data["email"], "password": "Mala#Clave1"}).status_code == 401
    r = c.post(LOGIN, json={"email": data["email"], "password": data["password"]})
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0


def test_me_requires_session(make_client):
    r = make_client().get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["success"] is False


def test_me_returns_decrypted_contact_data(register_user):
    c, data = register_user()
    r = c.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["data"]["email"] == data["email"]
    assert r.json()["data"]["phone"] == data["phone"]


def test_refresh_rotates_and_detects_reuse(register_user, make_client):
    c, _ = register_user()
    old_refresh = c.cookies.get("refresh_token")
    r = c.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert c.cookies.get("refresh_token") != old_refresh

    attacker = make_client()
    attacker.cookies.set("refresh_token", old_refresh, path="/api/v1/auth")
    assert attacker.post("/api/v1/auth/refresh").status_code == 401
    # La reutilización revoca todas las sesiones, incluida la legítima.
    assert c.post("/api/v1/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token(register_user):
    c, _ = register_user()
    refresh = c.cookies.get("refresh_token")
    r = c.post("/api/v1/auth/logout")
    assert r.status_code == 200
    c.cookies.set("refresh_token", refresh, path="/api/v1/auth")
    assert c.post("/api/v1/auth/refresh").status_code == 401


def test_tampered_or_none_alg_token_is_rejected(make_client):
    import base64
    import json

    def b64(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    forged = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': 'x', 'role': 'admin', 'iat': 1, 'exp': 9999999999})}."
    c = make_client()
    c.cookies.set("access_token", forged)
    assert c.get("/api/v1/admin/pets").status_code == 401


def test_user_cannot_access_admin_routes(register_user):
    c, _ = register_user()
    r = c.get("/api/v1/admin/pets")
    assert r.status_code == 403
