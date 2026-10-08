import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.main import Base, EventRow, create_app

KEY = "test-only-api-key-123456789"


@pytest.fixture
def client(tmp_path):
    app = create_app(os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}"), KEY)
    Base.metadata.create_all(app.state.engine)
    with app.state.engine.begin() as connection:
        connection.execute(EventRow.__table__.delete())
    with TestClient(app) as c:
        yield c


def event(**changes):
    return {"event_id": str(uuid4()), "source": "orders", "value": 42.5,
            "event_time": datetime.now(timezone.utc).isoformat(), **changes}


def post(client, data):
    return client.post("/v1/events", json=data, headers={"X-API-Key": KEY})


def test_persist_and_duplicate(client):
    data = event()
    assert post(client, data).status_code == 201
    assert post(client, data).status_code == 409
    response = client.get(f"/v1/events/{data['event_id']}", headers={"X-API-Key": KEY})
    assert response.status_code == 200
    assert response.json()["value"] == 42.5
    with client.app.state.engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(EventRow)) == 1
    assert 'dop_events_total{outcome="duplicate"} 1.0' in client.get("/metrics").text


@pytest.mark.parametrize("changes", [
    {"value": -1}, {"value": 1000001}, {"value": "NaN"}, {"source": "bad source"},
    {"event_id": "no"}, {"event_time": "2026-01-01T00:00:00"},
    {"event_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()},
    {"unexpected": "field"},
])
def test_reject(client, changes):
    assert post(client, event(**changes)).status_code == 422
    with client.app.state.engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(EventRow)) == 0
    assert 'dop_events_total{outcome="rejected"} 1.0' in client.get("/metrics").text


def test_auth(client):
    assert client.post("/v1/events", json=event()).status_code == 401
    assert client.get(f"/v1/events/{uuid4()}").status_code == 401


def test_stale_and_health(client):
    response = post(client, event(event_time=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()))
    assert response.status_code == 201
    assert response.json()["stale"]
    assert "dop_stale_events_total 1.0" in client.get("/metrics").text
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200


def test_database_failure(client):
    Base.metadata.drop_all(client.app.state.engine)
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    assert post(client, event()).status_code == 503
    assert 'dop_events_total{outcome="db_error"} 1.0' in client.get("/metrics").text


def test_missing(client):
    assert client.get(f"/v1/events/{uuid4()}", headers={"X-API-Key": KEY}).status_code == 404
