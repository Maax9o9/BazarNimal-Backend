from tests.helpers import make_png


def _create_pet(admin_client, name: str = "Firulais", species: str = "dog") -> dict:
    r = admin_client.post(
        "/api/v1/admin/pets",
        data={"name": name, "species": species, "breed": "Mestizo", "age_years": "2", "age_months": "3"},
        files={"image": ("foto.png", make_png(), "image/png")},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_admin_pet_crud(admin_client, uploads_dir):
    pet = _create_pet(admin_client, "Michi", "cat")
    assert pet["status"] == "in_adoption"
    assert pet["image_url"].startswith("http://testserver/uploads/images/pets/")
    assert pet["image_url"].endswith(".webp")
    first_file = uploads_dir / "pets" / pet["image_url"].rsplit("/", 1)[1]
    assert first_file.exists()

    r = admin_client.put(
        f"/api/v1/admin/pets/{pet['id']}",
        data={"name": "Michi", "species": "cat", "breed": "Siamés", "age_years": "3", "status": "in_adoption"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["breed"] == "Siamés"
    assert r.json()["data"]["image_url"] == pet["image_url"]

    r = admin_client.put(
        f"/api/v1/admin/pets/{pet['id']}",
        data={"name": "Michi", "species": "cat", "breed": "Siamés", "age_years": "3"},
        files={"image": ("nueva.png", make_png((10, 10, 10)), "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["data"]["image_url"] != pet["image_url"]
    assert not first_file.exists()  # la imagen anterior se borra del disco

    assert admin_client.delete(f"/api/v1/admin/pets/{pet['id']}").status_code == 200
    assert admin_client.get(f"/api/v1/admin/pets/{pet['id']}").status_code == 404


def test_pet_validation(admin_client):
    r = admin_client.post(
        "/api/v1/admin/pets",
        data={"name": "X", "species": "bird", "breed": "Y", "age_years": "-1"},
        files={"image": ("foto.png", b"not really a png", "image/png")},
    )
    assert r.status_code == 422
    fields = {error["field"] for error in r.json()["errors"]}
    assert {"species", "age_years", "image"} <= fields


def test_adoption_flow(admin_client, register_user, make_client):
    pet = _create_pet(admin_client, "Canelo")
    public = make_client()

    r = public.get("/api/v1/pets", params={"search": "Canelo"})
    assert r.status_code == 200
    assert any(item["id"] == pet["id"] for item in r.json()["data"])

    r = public.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]})
    assert r.status_code == 401  # solo usuarios registrados

    alice, alice_data = register_user("Alicia Gómez")
    bob, _ = register_user("Roberto Díaz")

    r = alice.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]})
    assert r.status_code == 201
    alice_request = r.json()["data"]
    assert alice_request["status"] == "pending"
    assert alice.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]}).status_code == 409
    assert bob.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]}).status_code == 201

    r = admin_client.get("/api/v1/admin/adoption-requests", params={"pet_id": pet["id"], "status": "pending"})
    assert r.status_code == 200
    requests = r.json()["data"]
    assert len(requests) == 2
    alice_row = next(item for item in requests if item["id"] == alice_request["id"])
    assert alice_row["applicant"] == {
        "id": alice_row["applicant"]["id"],
        "name": "Alicia Gómez",
        "email": alice_data["email"],
        "phone": "5512345678",
    }

    r = admin_client.patch(f"/api/v1/admin/adoption-requests/{alice_request['id']}/approve")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "approved"
    assert r.json()["data"]["pet"]["status"] == "adopted"

    bob_requests = bob.get("/api/v1/adoption-requests/me").json()["data"]
    assert bob_requests[0]["status"] == "rejected"  # se rechazan las demás pendientes

    assert public.get(f"/api/v1/pets/{pet['id']}").json()["data"]["status"] == "adopted"
    carl, _ = register_user()
    assert carl.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]}).status_code == 409
    r = admin_client.patch(f"/api/v1/admin/adoption-requests/{alice_request['id']}/approve")
    assert r.status_code == 409


def test_admin_cannot_request_adoption(admin_client):
    pet = _create_pet(admin_client, "Rocky")
    r = admin_client.post("/api/v1/adoption-requests", json={"pet_id": pet["id"]})
    assert r.status_code == 403


def test_invalid_uuid_and_pagination_limits(make_client):
    c = make_client()
    assert c.get("/api/v1/pets/not-a-uuid").status_code == 422
    r = c.get("/api/v1/pets", params={"limit": 500})
    assert r.status_code == 422
    r = c.get("/api/v1/pets", params={"sort": "name; DROP TABLE pets"})
    assert r.status_code == 422
