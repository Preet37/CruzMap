"""CruzSurge v2 backend: a thin Flask API around agent/cruzsurge_agent.py.
The user-facing page (web/index.html) never shows code or terminal output.
It only ever sees JSON results rendered into a polished UI."""

import os
import sys

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent.cruzsurge_agent import run_command, DEFAULT_STATE  # noqa: E402

app = Flask(__name__, static_folder=None)
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

SESSION_STATE = dict(DEFAULT_STATE)


@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(SESSION_STATE)


@app.route("/api/reset", methods=["POST"])
def reset_state():
    global SESSION_STATE
    SESSION_STATE = dict(DEFAULT_STATE)
    return jsonify(SESSION_STATE)


@app.route("/api/run", methods=["POST"])
def run_scenario():
    body = request.get_json(force=True)
    command = (body or {}).get("command", "").strip()
    fast = (body or {}).get("fast", True)
    if not command:
        return jsonify({"error": "empty command"}), 400

    result = run_command(command, SESSION_STATE, think=not fast)

    trace = []
    summary = None
    for entry in result["trace"]:
        if entry.get("tool_call"):
            trace.append({"type": "tool_call", "name": entry["tool_call"], "arguments": entry["arguments"]})
        elif entry.get("thinking"):
            trace.append({"type": "thinking", "text": entry["thinking"]})
        if entry.get("content"):
            summary = entry["content"]

    return jsonify(
        {
            "state": SESSION_STATE,
            "trace": trace,
            "summary": summary,
            "duration_sec": result["duration_sec"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8600, debug=False)
