"""Verify frozen SAT schedules and compressed per-orientation transcripts."""
import gzip
import hashlib
import json
import sys
from pathlib import Path


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def verify(directory):
    directory = Path(directory).resolve()
    cfg = json.loads((directory / "protocol.json").read_text())
    result = json.loads((directory / "result.json").read_text())
    assert result["protocol_sha256"] == sha_bytes((directory / "protocol.json").read_bytes())
    for source in cfg["sources"].values():
        assert sha_bytes(Path(source["path"]).read_bytes()) == source["sha256"]
    original = Path(cfg["sources"]["formula"]["path"]).read_bytes()
    header, rest = original.split(b"\n", 1)
    tag, fmt, variables, rows = header.split()
    assert (tag, fmt) == (b"p", b"cnf")
    attempts = result["orientations"]
    assert [r["orientation"] for r in attempts] == cfg["orientation_order"][:len(attempts)]
    assert result["script_sha256"] == cfg["sources"]["script"]["sha256"]
    assert result["solver_sha256"] == cfg["sources"]["solver"]["sha256"]
    for row in attempts:
        k = row["orientation"]
        selector = cfg["selector_wires"]
        units = b"".join(f"{wire if k >> bit & 1 else -wire} 0\n".encode()
                         for bit, wire in enumerate(selector))
        formula = b" ".join((tag, fmt, variables, str(int(rows) + 6).encode())) + b"\n" + rest + units
        assert sha_bytes(formula) == row["formula_sha256"]
        out = gzip.open(directory / f"orientation_{k:02d}.stdout.gz", "rb").read()
        err = gzip.open(directory / f"orientation_{k:02d}.stderr.gz", "rb").read()
        assert sha_bytes(out) == row["stdout_sha256"]
        assert sha_bytes(err) == row["stderr_sha256"]
        lines = out.decode(errors="replace").splitlines()
        assert row["terminal_sat_line"] == any(s.strip() == "s SATISFIABLE" for s in lines)
        assert row["terminal_unsat_line"] == any(s.strip() == "s UNSATISFIABLE" for s in lines)
        assert not (row["terminal_sat_line"] and row["terminal_unsat_line"])
    if result["status"] == "SCHEDULE_EXHAUSTED":
        assert len(attempts) == 41
        assert all(not r["terminal_sat_line"] for r in attempts)
    print(json.dumps({"status": "PASS_SCHEDULE_ARCHIVE", "path": str(directory),
                      "attempts": len(attempts), "result_status": result["status"]}, sort_keys=True))


if __name__ == "__main__":
    assert len(sys.argv) == 2
    verify(sys.argv[1])
