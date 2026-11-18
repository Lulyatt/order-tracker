import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

REPO_DIR = Path(os.getenv("RESPONDER_REPO_DIR", HERE.parent)).resolve()
INCIDENTS_DIR = Path(os.getenv("RESPONDER_INCIDENTS_DIR", HERE / "incidents")).resolve()

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")
SERVICE_NAME = os.getenv("RESPONDER_SERVICE_NAME", "order-tracker")
LOOKBACK_MINUTES = int(os.getenv("RESPONDER_LOOKBACK_MINUTES", "15"))

if sys.platform == "win32":
    _default_agent = Path(os.environ.get("LOCALAPPDATA", "")) / "cursor-agent" / "agent.cmd"
else:
    _default_agent = Path("agent")
AGENT_BIN = os.getenv("RESPONDER_AGENT_BIN", str(_default_agent))
AGENT_MODEL = os.getenv("RESPONDER_MODEL", "")
AGENT_TIMEOUT_SECONDS = int(os.getenv("RESPONDER_AGENT_TIMEOUT", "900"))