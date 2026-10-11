"""Bounded searches on the frozen conditional-image formulas."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_CONDITIONAL_IMAGE_EXACT_N41"
    assert p["source_sha256"]["circuit"] == sha(HERE / "circuit.py")
    assert p["source_sha256"]["prepare"] == sha(HERE / "prepare.py")
    assert p["solver_sha256"] == sha(p["solver"])
    for label, shape in p["cases"].items():
        assert shape["sha256"] == sha(HERE / f"{label}.xcnf")
    identity = {"status": "FROZEN_BEFORE_SOLVES", "protocol_sha256": sha(HERE / "protocol.json"),
                "runner_sha256": sha(__file__), "cases": list(p["cases"])}
    path = HERE / "solver_protocol.json"
    if path.exists():
        assert json.loads(path.read_text()) == identity
    else:
        save(path, identity)
    for label in identity["cases"]:
        start = time.monotonic_ns()
        with (HERE / f"{label}.stdout").open("wb") as out, \
             (HERE / f"{label}.stderr").open("wb") as err:
            child = subprocess.Popen([p["solver"], *p["solver_flags"],
                                      str(HERE / f"{label}.xcnf")], stdout=out, stderr=err)
            proc = psutil.Process(child.pid)
            parent = psutil.Process()
            peak = 0
            killed = None
            while child.poll() is None:
                try:
                    rss = proc.memory_info().rss + parent.memory_info().rss
                except psutil.NoSuchProcess:
                    rss = parent.memory_info().rss
                peak = max(peak, rss)
                if rss > p["rss_cap_bytes"]:
                    killed = "RSS_CAP"
                    child.kill()
                    break
                if (time.monotonic_ns() - start) / 1e9 > p["parent_cap_seconds"]:
                    killed = "PARENT_TIME_CAP"
                    child.kill()
                    break
                time.sleep(0.1)
            code = child.wait()
        elapsed = time.monotonic_ns() - start
        stdout = (HERE / f"{label}.stdout").read_bytes()
        if killed == "RSS_CAP":
            status = "RESOURCE_GATE_EXCEEDED"
        elif b"s UNSATISFIABLE" in stdout:
            status = "UNSAT"
        elif b"s SATISFIABLE" in stdout:
            status = "SAT_MODEL"
        else:
            status = "BOUNDED_UNKNOWN"
        record = {"label": label, "status": status, "return_code": code,
                  "killed_by": killed, "wall_ns": elapsed,
                  "peak_combined_rss_bytes": peak,
                  "stdout_sha256": sha(HERE / f"{label}.stdout"),
                  "stderr_sha256": sha(HERE / f"{label}.stderr"),
                  "solver_protocol_sha256": sha(path),
                  "search_started": b"c [branch]" in stdout or b"c [scc]" in stdout
                                    or b"c [xor]" in stdout or b"c [conflicts]" in stdout}
        save(HERE / f"{label}.json", record)
        print(label, status, round(elapsed / 1e9, 3), peak, flush=True)


if __name__ == "__main__":
    main()
