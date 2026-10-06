from tests.helpers import make_png


def test_product_crud_with_optional_fields(admin_client, make_client):
    r = admin_client.post(
        "/api/v1/admin/products",
        data={"name": "Croquetas premium", "weight_kg": "15.5"},
        files={"image": ("croquetas.png", make_png(), "image/png")},
    )
    assert r.status_code == 201, r.text
    product = r.json()["data"]
    assert product["weight_kg"] == "15.500"
    assert product["pieces"] is None
    assert product["status"] == "available"

    r = admin_client.put(
        f"/api/v1/admin/products/{product['id']}",
        data={"name": "Croquetas premium", "pieces": "3", "weight_kg": "", "status": "unavailable"},
    )
    assert r.status_code == 200, r.text
    updated = r.json()["data"]
    assert updated["weight_kg"] is None
    assert updated["pieces"] == 3
    assert updated["status"] == "unavailable"

    public = make_client()
    r = public.get("/api/v1/products", params={"status": "unavailable", "search": "Croquetas"})
    assert r.status_code == 200
    assert any(item["id"] == product["id"] for item in r.json()["data"])
    assert "created_at" not in r.json()["data"][0]

    assert admin_client.delete(f"/api/v1/admin/products/{product['id']}").status_code == 200
    assert public.get(f"/api/v1/products/{product['id']}").status_code == 404


def test_product_validation(admin_client):
    r = admin_client.post(
        "/api/v1/admin/products",
        data={"name": "Juguete", "weight_kg": "-2", "pieces": "0"},
        files={"image": ("j.png", make_png(), "image/png")},
    )
    assert r.status_code == 422
    fields = {error["field"] for error in r.json()["errors"]}
    assert {"weight_kg", "pieces"} <= fields


def test_search_wildcards_are_escaped(admin_client, make_client):
    admin_client.post(
        "/api/v1/admin/products",
        data={"name": "Correa 100% nylon"},
        files={"image": ("c.png", make_png(), "image/png")},
    )
    public = make_client()
    names = [p["name"] for p in public.get("/api/v1/products", params={"search": "100%"}).json()["data"]]
    assert "Correa 100% nylon" in names
    assert public.get("/api/v1/products", params={"search": "%"}).json()["meta"]["total"] >= 1
    assert public.get("/api/v1/products", params={"search": "_zz_"}).json()["meta"]["total"] == 0
