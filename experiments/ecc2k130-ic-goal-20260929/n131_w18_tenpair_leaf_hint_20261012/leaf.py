"""Constructed-target leaf-information profile on archived ten-pair XCNF."""

import gzip
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_tenpair_hint_profile_20261012"
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
sys.path.insert(0, str(PARENT))
import profile as prior  # noqa: E402

ten = prior.ten
ARMS = ("output10", "selector10", "selector10_output10",
        "selector10_output10_intermediate8")
CAP = 60
RSS_CAP = 4 * 1024**3
FLAGS = ("--threads=1", "--maxtime=55", "--zero-exit-status", "--verb=1", "--printsol=1")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def inputs():
    fixture = json.loads((SOURCE / "control_fixture.json").read_text())
    prior_fixture = json.loads((ten.NINE / "control_fixture.json").read_text())
    points = ten.witness_points(prior_fixture) + [tuple(fixture["last_pair_point"])]
    nodes = list(points)
    intermediate = []
    for left, right in ten.TREE:
        point = ten.independent.point_add(nodes[left], nodes[right])
        assert point is not None and point[0] != 0
        nodes.append(point)
        if len(intermediate) < 8:
            intermediate.append(ten.independent.inverse(point[0]))
    assert nodes[-1] == tuple(fixture["raw_target"])
    circuit, wires, _ = prior.build_hints()
    bindings = {"target": [], "selectors": [], "outputs": [], "intermediates": []}
    for wire in wires["fiber_bits"] + wires["rotation_bits"]:
        bindings["target"].append(-wire)
    def add_bits(kind, bit_wires, value):
        bindings[kind].extend(wire if value >> bit & 1 else -wire
                              for bit, wire in enumerate(bit_wires))
    for slot, item in enumerate(fixture["selected"]):
        assert item["slot"] == slot
        add_bits("selectors", wires["selectors"][slot],
                 ten.pair.selector_code(item["masks"][0]))
        add_bits("outputs", wires["outputs"][slot],
                 ten.base.standard_reciprocal(item["unrotated_pair_output_z"]))
    for bits, value in zip(wires["intermediates"], intermediate):
        add_bits("intermediates", bits, value)
    assert {key: len(value) for key, value in bindings.items()} == {
        "target": 10, "selectors": 170, "outputs": 1310, "intermediates": 1048}
    return circuit, bindings


def units_for(arm, bindings):
    kinds = ["target"]
    if "selector10" in arm:
        kinds.append("selectors")
    if "output10" in arm:
        kinds.append("outputs")
    if "intermediate8" in arm:
        kinds.append("intermediates")
    return [literal for kind in kinds for literal in bindings[kind]]


def variant(raw, units, path):
    header, tail = raw.split(b"\n", 1)
    parts = header.split()
    assert parts[:2] == [b"p", b"cnf"]
    payload = (f"p cnf {int(parts[2])} {int(parts[3])+len(units)}\n".encode() +
               tail + b"".join(f"{literal} 0\n".encode() for literal in units))
    path.write_bytes(payload)
    return {"unit_clauses": len(units), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def freeze():
    result = json.loads((PARENT / "result.json").read_text())
    assert result["status"] == "COMPLETE_CONSTRUCTED_HINT_PROFILE"
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_LEAF_HINT_PROFILE", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "point_law": "constructed ten-pair control point",
        "arms": ARMS, "cap_seconds_per_arm": CAP,
        "combined_rss_cap_bytes": RSS_CAP, "workers": 1,
        "solver_flags": FLAGS,
        "source_hashes": {str(path): sha(path) for path in
                          (SOURCE / "control.xcnf.gz", SOURCE / "control_fixture.json",
                           SOURCE / "control_result.json", PARENT / "profile.py",
                           PARENT / "result.json", Path(__file__), ten.base.SOLVER)},
        "raw_parent_sha256": prior.RAW_HASH,
    })


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_LEAF_HINT_PROFILE"
    for path, digest in protocol["source_hashes"].items():
        assert sha(path) == digest, path
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == prior.RAW_HASH
    circuit, bindings = inputs()
    regenerated = HERE / "regenerated.xcnf"
    circuit.write(regenerated)
    assert sha(regenerated) == prior.RAW_HASH
    regenerated.unlink()
    rows = []
    for arm in ARMS:
        path = HERE / f"{arm}.xcnf"
        formula = variant(raw, units_for(arm, bindings), path)
        outpath, errpath = HERE / f"{arm}.stdout", HERE / f"{arm}.stderr"
        peak, stop = 0, None
        parent = psutil.Process()
        start = time.monotonic_ns()
        with outpath.open("x") as stdout, errpath.open("x") as stderr:
            child = subprocess.Popen([str(ten.base.SOLVER), *FLAGS, str(path)],
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
        archive = HERE / f"{arm}.xcnf.gz"
        with archive.open("xb") as out:
            with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0, compresslevel=6) as gz:
                gz.write(path.read_bytes())
        path.unlink()
        row = {"arm": arm, "status": status, "terminal": terminals[-1] if terminals else None,
               "stop": stop, "exit_code": exit_code, "solver_wall_ns": elapsed,
               "peak_combined_rss_bytes": peak, "restart_rows": sum(x.startswith("c rst") for x in lines),
               "formula": formula, "archive_sha256": sha(archive),
               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath)}
        rows.append(row)
        print(json.dumps({key: row[key] for key in ("arm", "status", "solver_wall_ns", "restart_rows")}), flush=True)
    save(HERE / "result.json", {"status": "COMPLETE_LEAF_HINT_PROFILE",
                                "protocol_sha256": sha(HERE / "protocol.json"), "arms": rows})


def verify():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    for path, digest in protocol["source_hashes"].items():
        assert sha(path) == digest
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == prior.RAW_HASH
    _, bindings = inputs()
    for arm, row in zip(ARMS, result["arms"]):
        assert row["arm"] == arm
        path = HERE / f"{arm}.xcnf"
        assert variant(raw, units_for(arm, bindings), path) == row["formula"]
        with gzip.open(HERE / f"{arm}.xcnf.gz", "rb") as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == row["formula"]["sha256"]
        path.unlink()
        assert sha(HERE / f"{arm}.stdout") == row["stdout_sha256"]
        assert sha(HERE / f"{arm}.stderr") == row["stderr_sha256"]
        lines = (HERE / f"{arm}.stdout").read_text(errors="replace").splitlines()
        assert sum(x.startswith("c rst") for x in lines) == row["restart_rows"]
        assert row["peak_combined_rss_bytes"] < RSS_CAP
        assert row["status"] in ("SAT", "BOUNDED_UNKNOWN")
    print("PASS_N131_TENPAIR_LEAF_HINT_PROFILE", len(ARMS))


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
