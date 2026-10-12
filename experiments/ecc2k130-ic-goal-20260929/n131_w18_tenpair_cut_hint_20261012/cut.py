"""Which exact upper-tree cut makes the constructed ten-pair formula complete?"""

import gzip
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
LEAF = HERE.parent / "n131_w18_tenpair_leaf_hint_20261012"
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
sys.path.insert(0, str(LEAF))
import leaf  # noqa: E402

ARMS = {"final7": (7,), "root6": (6,), "pretarget6_7": (6, 7),
        "middle4_5": (4, 5), "bottom0_3": (0, 1, 2, 3)}
CAP = 60
RSS_CAP = 4 * 1024**3
FLAGS = ("--threads=1", "--maxtime=55", "--zero-exit-status", "--verb=1", "--printsol=1")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, indent=2, sort_keys=True)
        stream.write("\n")


def freeze():
    parent = json.loads((LEAF / "result.json").read_text())
    assert parent["arms"][2]["status"] == "BOUNDED_UNKNOWN"
    assert parent["arms"][3]["status"] == "SAT"
    sources = (Path(__file__), LEAF / "leaf.py", LEAF / "result.json",
               SOURCE / "control.xcnf.gz", SOURCE / "control_fixture.json",
               SOURCE / "sage_fixture_result.json", leaf.ten.base.SOLVER)
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_CUT_HINT_PROFILE", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "point_law": "constructed ten-pair control point",
        "base_hints": "target choice, all ten pair selectors, all ten pair outputs",
        "tree": leaf.ten.TREE, "arms": ARMS,
        "workers": 1, "cap_seconds_per_arm": CAP,
        "combined_rss_cap_bytes": RSS_CAP, "solver_flags": FLAGS,
        "sources": {str(path): sha(path) for path in sources},
        "raw_parent_sha256": leaf.prior.RAW_HASH,
    })


def arm_units(name, binding):
    units = leaf.units_for("selector10_output10", binding)
    upper = binding["intermediates"]
    for node in ARMS[name]:
        units.extend(upper[node * 131:(node + 1) * 131])
    return units


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_CUT_HINT_PROFILE"
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == leaf.prior.RAW_HASH
    circuit, binding = leaf.inputs()
    regenerated = HERE / "regenerated.xcnf"
    circuit.write(regenerated)
    assert sha(regenerated) == leaf.prior.RAW_HASH
    regenerated.unlink()
    rows = []
    for name, nodes in ARMS.items():
        path = HERE / f"{name}.xcnf"
        formula = leaf.variant(raw, arm_units(name, binding), path)
        outpath, errpath = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
        parent = psutil.Process()
        peak, stop = 0, None
        start = time.monotonic_ns()
        with outpath.open("x") as stdout, errpath.open("x") as stderr:
            child = subprocess.Popen([str(leaf.ten.base.SOLVER), *FLAGS, str(path)],
                                     stdout=stdout, stderr=stderr)
            proc = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    rss = parent.memory_info().rss + proc.memory_info().rss
                    peak = max(peak, rss)
                    if rss > RSS_CAP:
                        stop = "RSS_CAP"
                except psutil.NoSuchProcess:
                    pass
                if (time.monotonic_ns() - start) / 1e9 > CAP:
                    stop = "WALL_CAP"
                if stop:
                    child.kill()
                    break
                time.sleep(0.025)
            exit_code = child.wait()
        elapsed = time.monotonic_ns() - start
        lines = outpath.read_text(errors="replace").splitlines()
        terminals = [line for line in lines if line.startswith("s ")]
        status = ("SAT" if terminals and terminals[-1] == "s SATISFIABLE" else
                  "UNSAT" if terminals and terminals[-1] == "s UNSATISFIABLE" else
                  "BOUNDED_UNKNOWN")
        archive = HERE / f"{name}.xcnf.gz"
        with archive.open("xb") as out:
            with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0, compresslevel=6) as gz:
                gz.write(path.read_bytes())
        path.unlink()
        row = {"arm": name, "nodes": nodes, "status": status,
               "terminal": terminals[-1] if terminals else None,
               "stop": stop, "exit_code": exit_code,
               "solver_wall_ns": elapsed, "peak_combined_rss_bytes": peak,
               "restart_rows": sum(x.startswith("c rst") for x in lines),
               "formula": formula, "archive_sha256": sha(archive),
               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath)}
        rows.append(row)
        print(json.dumps({key: row[key] for key in
                          ("arm", "status", "solver_wall_ns", "restart_rows")}), flush=True)
    save(HERE / "result.json", {"status": "COMPLETE_CUT_HINT_PROFILE",
                                "protocol_sha256": sha(HERE / "protocol.json"), "arms": rows})


def verify():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert sha(HERE / "protocol.json") == result["protocol_sha256"]
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == leaf.prior.RAW_HASH
    _, binding = leaf.inputs()
    for (name, nodes), row in zip(ARMS.items(), result["arms"]):
        assert row["arm"] == name and row["nodes"] == list(nodes)
        path = HERE / f"{name}.xcnf"
        assert leaf.variant(raw, arm_units(name, binding), path) == row["formula"]
        with gzip.open(HERE / f"{name}.xcnf.gz", "rb") as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == row["formula"]["sha256"]
        path.unlink()
        assert sha(HERE / f"{name}.stdout") == row["stdout_sha256"]
        assert sha(HERE / f"{name}.stderr") == row["stderr_sha256"]
        lines = (HERE / f"{name}.stdout").read_text(errors="replace").splitlines()
        assert sum(x.startswith("c rst") for x in lines) == row["restart_rows"]
        assert row["peak_combined_rss_bytes"] < RSS_CAP
        assert row["status"] in ("SAT", "BOUNDED_UNKNOWN")
    print("PASS_N131_TENPAIR_CUT_HINT_PROFILE", len(ARMS))


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
