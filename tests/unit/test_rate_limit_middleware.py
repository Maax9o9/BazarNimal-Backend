from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.security.rate_limit import InMemoryRateLimitStore
from src.core.server.middlewares import GlobalRateLimitMiddleware


def _client(read_limit: int, write_limit: int) -> TestClient:
    app = FastAPI()

    @app.get("/items")
    def list_items() -> dict:
        return {"ok": True}

    @app.post("/items")
    def create_item() -> dict:
        return {"ok": True}

    app.add_middleware(
        GlobalRateLimitMiddleware,
        store=InMemoryRateLimitStore(),
        read_policy=(read_limit, 900),
        write_policy=(write_limit, 900),
    )
    return TestClient(app)


def test_reads_and_writes_have_separate_limits():
    client = _client(read_limit=3, write_limit=1)

    assert client.post("/items").status_code == 200
    assert client.post("/items").status_code == 429  # escritura agotada

    # Las lecturas siguen funcionando aunque la escritura esté bloqueada.
    responses = [client.get("/items") for _ in range(3)]
    assert [r.status_code for r in responses] == [200, 200, 200]
    assert responses[-1].headers["RateLimit-Limit"] == "3"
    assert responses[-1].headers["RateLimit-Remaining"] == "0"

    blocked = client.get("/items")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
