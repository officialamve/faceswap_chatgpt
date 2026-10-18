from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.health import router

def test_health_endpoint():
    app = FastAPI(); app.include_router(router)
    c = TestClient(app)
    assert c.get('/healthz').status_code == 200
    assert c.get('/readyz').status_code == 503
    app.state.ready = True
    assert c.get('/readyz').status_code == 200
