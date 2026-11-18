# Incident responder

Grafana webhook receiver for Order Tracker (Homework 4, Question 5).

On each firing alert it:

1. Saves `incidents/<id>/alert.json`
2. Collects metrics, logs and traces via Grafana (`context.md` + JSON files)
3. Runs the Cursor Agent CLI (`agent -p`) to investigate

## Prerequisites

- Docker Compose stack running (Grafana on port 3000)
- [Cursor Agent CLI](https://cursor.com/cli) installed (`%LOCALAPPDATA%\cursor-agent\agent.cmd` on Windows)
- `agent login` or `CURSOR_API_KEY` set

## Run locally

```bash
cd incident-response
uv sync
uv run uvicorn responder.main:app --host 127.0.0.1 --port 8001
```

## Homework test alert

```bash
curl -X POST http://127.0.0.1:8001/alerts \
  -H "Content-Type: application/json" \
  -d "{\"alerts\":[{\"status\":\"firing\",\"labels\":{\"alertname\":\"ResponderTest\",\"test\":\"true\"},\"annotations\":{\"summary\":\"Test notification; no incident to fix\"}}]}"
```

Wait until the agent finishes, then:

```bash
curl http://127.0.0.1:8001/incidents
curl http://127.0.0.1:8001/incidents/<incident_id>
```

Read `incidents/<incident_id>/response.md` for the agent answer (last line should be `STATUS: TEST_ACKNOWLEDGED`).

## Configuration

| Variable | Default |
| --- | --- |
| `GRAFANA_URL` | `http://localhost:3000` |
| `RESPONDER_REPO_DIR` | Order Tracker repo root (parent of this folder) |
| `RESPONDER_AGENT_BIN` | `%LOCALAPPDATA%\cursor-agent\agent.cmd` (Windows) |
| `RESPONDER_MODEL` | Cursor CLI default |
| `RESPONDER_AGENT_TIMEOUT` | `900` |

Tests: `uv run --frozen pytest -q`

## Grafana webhook (Question 6)

With the Compose stack running, start this responder on the host (`127.0.0.1:8001`). Grafana posts 5xx alerts to `http://host.docker.internal:8001/alerts` (see `observability/grafana/provisioning/alerting/notifications.yaml`).

Trigger the incident:

```bash
curl -i http://localhost:8000/api/orders/express-1002
```

After the agent fixes the app, rebuild and verify:

```bash
docker compose up --build -d --wait
curl -i http://localhost:8000/api/orders/express-1002
```