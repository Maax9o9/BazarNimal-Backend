def test_swagger_and_openapi_are_available(make_client):
    c = make_client()
    assert c.get("/docs").status_code == 200
    spec = c.get("/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/admin/adoption-requests/{request_id}/approve" in paths
    create_pet = paths["/api/v1/admin/pets"]["post"]
    schema_ref = create_pet["requestBody"]["content"]["multipart/form-data"]["schema"]["$ref"]
    form = spec["components"]["schemas"][schema_ref.rsplit("/", 1)[1]]
    assert form["properties"]["image"].get("format") == "binary" or "contentMediaType" in form["properties"]["image"]
    assert "access_token" in str(spec["components"]["securitySchemes"])
