"""Check frozen source, XCNF, solver logs, and capped statuses."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    sp = json.loads((HERE / "solver_protocol.json").read_text())
    assert p["status"] == "FROZEN_CONDITIONAL_IMAGE_EXACT_N41"
    assert p["images"] == {"20": {"seeds": 63, "image_size_each": 31,
                                  "parity_rows_each": 6},
                            "30": {"seeds": 63, "image_size_each": 31,
                                  "parity_rows_each": 6}}
    assert all(sha(HERE / name) == digest for name, digest in
               (("circuit.py", p["source_sha256"]["circuit"]),
                ("prepare.py", p["source_sha256"]["prepare"]),
                ("solve.py", sp["runner_sha256"])))
    assert sha(p["solver"]) == p["solver_sha256"]
    assert sha(HERE / "protocol.json") == sp["protocol_sha256"]
    checks = {}
    for label in sp["cases"]:
        shape = p["cases"][label]
        result = json.loads((HERE / f"{label}.json").read_text())
        stdout = (HERE / f"{label}.stdout").read_bytes()
        assert sha(HERE / f"{label}.xcnf") == shape["sha256"]
        assert sha(HERE / f"{label}.stdout") == result["stdout_sha256"]
        assert sha(HERE / f"{label}.stderr") == result["stderr_sha256"]
        assert result["solver_protocol_sha256"] == sha(HERE / "solver_protocol.json")
        assert result["status"] == "BOUNDED_UNKNOWN"
        assert result["killed_by"] == "PARENT_TIME_CAP"
        assert result["search_started"]
        assert b"s SATISFIABLE" not in stdout and b"s UNSATISFIABLE" not in stdout
        assert 35e9 <= result["wall_ns"] <= 36e9
        assert result["peak_combined_rss_bytes"] < p["rss_cap_bytes"]
        checks[label] = {"status": result["status"],
                         "wall_seconds": result["wall_ns"] / 1e9,
                         "peak_combined_rss_bytes": result["peak_combined_rss_bytes"]}
    out = {"status": "PASS_FROZEN_EXACT_IMAGE_CAP_AUDIT", "cases": checks,
           "protocol_sha256": sha(HERE / "protocol.json"),
           "solver_protocol_sha256": sha(HERE / "solver_protocol.json")}
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
