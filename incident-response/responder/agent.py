"""Run the Cursor Agent CLI in headless mode against an incident folder."""

import json
import subprocess
import sys

from responder import config

PROMPT = """\
You are the on-call engineer for the Order Tracker service. A Grafana alert just reached
the incident responder. The repository is the current working directory.

Everything collected for this alert is in {incident_dir}:
- context.md: alert details, affected endpoint, request counts, error logs, failing traces
- alert.json, metrics.json, logs.json, traces.json: the raw data behind context.md

Steps:
1. Read context.md first.
2. If the alert is a test (label test="true") or there is no incident to investigate, say so in
 one or two sentences and stop. Do not investigate further.
3. Otherwise find the root cause. Use the logs, traces and stack traces, then read the code.
4. If the cause is a bug in this repository's code and the fix is small and clear:
 - fix it with the smallest change,
 - add a regression test in tests/,
 - run `uv run --frozen pytest -q` and make sure everything passes.
 Do not commit, restart containers or deploy.

Answer in Markdown. End with exactly one final line, one of:
STATUS: TEST_ACKNOWLEDGED
STATUS: FIXED
STATUS: ROOT_CAUSE_FOUND
STATUS: ESCALATE
"""


def build_prompt(incident_dir):
    return PROMPT.format(incident_dir=incident_dir)


def build_argv(incident_dir):
    argv = [
        str(config.AGENT_BIN),
        "-p",
        "--output-format",
        "json",
        "--trust",
        "--workspace",
        str(config.REPO_DIR),
        "--add-dir",
        str(incident_dir),
    ]
    if config.AGENT_MODEL:
        argv += ["--model", config.AGENT_MODEL]
    return argv


def run_argv(argv, prompt):
    if sys.platform == "win32" and str(config.AGENT_BIN).lower().endswith(".cmd"):
        return subprocess.run(
            ["cmd.exe", "/c", *argv],
            cwd=config.REPO_DIR,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=config.AGENT_TIMEOUT_SECONDS,
        )
    return subprocess.run(
        argv,
        cwd=config.REPO_DIR,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=config.AGENT_TIMEOUT_SECONDS,
    )


def parse_answer(stdout, stderr):
    text = stdout.strip()
    try:
        output = json.loads(text)
        if isinstance(output, dict):
            for key in ("result", "text", "response"):
                if output.get(key):
                    return str(output[key])
    except json.JSONDecodeError:
        pass
    return text or stderr


def run_agent(incident_dir):
    prompt = build_prompt(incident_dir)
    completed = run_argv(build_argv(incident_dir), prompt)
    (incident_dir / "agent-output.json").write_text(
        json.dumps({"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}, indent=2)
    )
    answer = parse_answer(completed.stdout, completed.stderr)
    (incident_dir / "response.md").write_text(answer + "\n")
    if completed.returncode != 0 and not answer.strip():
        raise RuntimeError(f"agent exited with code {completed.returncode}: {completed.stderr[:500]}")
    return answer