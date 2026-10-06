from tests.helpers import make_png


def _create_post(client, content: str = "Mi perrito de catrín") -> dict:
    r = client.post(
        "/api/v1/posts",
        data={"content": content},
        files={"image": ("disfraz.png", make_png((250, 120, 0)), "image/png")},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


def test_post_moderation_flow(register_user, admin_client, make_client):
    author, _ = register_user("Lupita Hernández")
    post = _create_post(author, "Catrina felina 🐱💀")
    assert post["status"] == "pending"
    assert post["author_name"] == "Lupita Hernández"

    public = make_client()
    approved_ids = [p["id"] for p in public.get("/api/v1/posts").json()["data"]]
    assert post["id"] not in approved_ids
    assert public.get(f"/api/v1/posts/{post['id']}").status_code == 404

    pending = admin_client.get("/api/v1/admin/posts", params={"status": "pending"}).json()["data"]
    assert any(p["id"] == post["id"] for p in pending)

    r = admin_client.patch(f"/api/v1/admin/posts/{post['id']}/approve")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "approved"
    assert admin_client.patch(f"/api/v1/admin/posts/{post['id']}/approve").status_code == 409

    visible = public.get(f"/api/v1/posts/{post['id']}")
    assert visible.status_code == 200
    assert visible.json()["data"]["author_name"] == "Lupita Hernández"
    assert "status" not in visible.json()["data"]

    assert admin_client.patch(f"/api/v1/admin/posts/{post['id']}/reject").status_code == 200
    assert public.get(f"/api/v1/posts/{post['id']}").status_code == 404

    mine = author.get("/api/v1/posts/me").json()["data"]
    assert mine[0]["status"] == "rejected"


def test_user_cannot_delete_someone_elses_post(register_user):
    owner, _ = register_user()
    intruder, _ = register_user()
    post = _create_post(owner)
    assert intruder.delete(f"/api/v1/posts/{post['id']}").status_code == 404
    assert owner.delete(f"/api/v1/posts/{post['id']}").status_code == 200


def test_post_requires_registered_user(make_client):
    r = make_client().post(
        "/api/v1/posts",
        data={"content": "hola"},
        files={"image": ("x.png", make_png(), "image/png")},
    )
    assert r.status_code == 401


def test_post_rejects_disguised_file(register_user):
    c, _ = register_user()
    r = c.post(
        "/api/v1/posts",
        data={"content": "virus"},
        files={"image": ("foto.png", b"<?php system($_GET['c']); ?>", "image/png")},
    )
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "image"
