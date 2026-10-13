"""Classify the frozen first XCNF producer attempt from its terminal bytes."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


result = {"status": "PRODUCER_FAILURE_XCNF_ZERO_LITERAL",
          "candidate_id": None, "attempts": {},
          "source_sha256": sha(HERE / "run.py"),
          "protocol_sha256": sha(HERE / "protocol.json")}
for label in ("control", "public"):
    receipt = read(HERE / f"{label}.json")
    profile = read(HERE / f"{label}.build.json")
    formula = HERE / f"{label}.xcnf"
    stdout, stderr = HERE / f"{label}.stdout", HERE / f"{label}.stderr"
    assert profile["sha256"] == sha(formula)
    assert profile["bytes"] == formula.stat().st_size
    assert receipt["status"] == "UNKNOWN" and receipt["exit_code"] == 255
    assert receipt["terminal_lines"] == [] and receipt["restart_rows"] == 0
    assert receipt["stdout_sha256"] == sha(stdout)
    assert receipt["stderr_sha256"] == sha(stderr)
    error = stderr.read_text()
    assert "PARSE ERROR! Unexpected char (hex: 0x32)" in error
    malformed = [(number, line) for number, line in enumerate(formula.read_text().splitlines(), 1)
                 if line.startswith("0 ")]
    assert len(malformed) == 1 and malformed[0][0] == 112221
    assert malformed[0][1].split()[-1] == "0"
    result["attempts"][label] = {
        "receipt_sha256": sha(HERE / f"{label}.json"),
        "formula_sha256": sha(formula),
        "stderr_sha256": sha(stderr),
        "malformed_line": malformed[0][0],
        "solver_exit_code": 255,
        "solver_search_started": False,
    }
with (HERE / "failure_audit_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], flush=True)
