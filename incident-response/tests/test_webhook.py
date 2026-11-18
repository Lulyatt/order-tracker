import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from responder import config
from responder.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INCIDENTS_DIR", tmp_path)
    with TestClient(app) as test_client:
        yield test_client


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def _fake_agent(incident_dir):
    text = "Acknowledged.\nSTATUS: TEST_ACKNOWLEDGED\n"
    (incident_dir / "response.md").write_text(text)
    return text


@patch("responder.main.collect")
@patch("responder.main.run_agent", side_effect=_fake_agent)
def test_alerts_queues_investigation(mock_agent, mock_collect, client, tmp_path):
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "ResponderTest", "test": "true"},
                "annotations": {"summary": "Test notification"},
            }
        ]
    }
    response = client.post("/alerts", json=payload)
    assert response.status_code == 202
    incident_id = response.json()["incidents"][0]["id"]
    incident_dir = tmp_path / incident_id
    assert (incident_dir / "alert.json").is_file()

    client.app.state  # keep app alive while worker runs
    import time
    for _ in range(50):
        status = json.loads((incident_dir / "status.json").read_text())
        if status.get("state") in {"done", "failed", "skipped"}:
            break
        time.sleep(0.05)

    assert status["state"] == "done"
    assert status["last_line"] == "STATUS: TEST_ACKNOWLEDGED"
    mock_collect.assert_called_once()
    mock_agent.assert_called_once()
    detail = client.get(f"/incidents/{incident_id}").json()
    assert "STATUS: TEST_ACKNOWLEDGED" in (detail.get("response") or "")