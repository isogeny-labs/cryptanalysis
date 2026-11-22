"""Frozen constructed-target branch-bit profile for the ten-pair XCNF."""

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

ARMS = {
    "all9_with_outputs": {"selectors": True, "outputs": True, "branch_ids": tuple(range(9))},
    "all9_no_outputs": {"selectors": True, "outputs": False, "branch_ids": tuple(range(9))},
    "first4_with_outputs": {"selectors": True, "outputs": True, "branch_ids": tuple(range(4))},
    "last5_with_outputs": {"selectors": True, "outputs": True, "branch_ids": tuple(range(4, 9))},
}
CAP = 60
RSS_CAP = 4 * 1024**3
FLAGS = ("--threads=1", "--maxtime=55", "--zero-exit-status", "--verb=1", "--printsol=1")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def bindings():
    circuit, wires, _ = leaf.prior.build_hints()
    fixture = json.loads((SOURCE / "control_result.json").read_text())
    bits = fixture["branch_bits"]
    assert len(bits) == len(wires["branches"]) == 9
    assert all(bit in (0, 1) for bit in bits)
    _, leaf_binding = leaf.inputs()
    branches = [wire if bit else -wire for wire, bit in zip(wires["branches"], bits)]
    return circuit, leaf_binding, branches, bits


def arm_units(name, common, branches):
    arm = ARMS[name]
    units = list(common["target"])
    if arm["selectors"]:
        units.extend(common["selectors"])
    if arm["outputs"]:
        units.extend(common["outputs"])
    units.extend(branches[index] for index in arm["branch_ids"])
    return units


def freeze():
    parent = json.loads((LEAF / "result.json").read_text())
    assert parent["arms"][2]["status"] == "BOUNDED_UNKNOWN"
    assert parent["arms"][3]["status"] == "SAT"
    sources = (Path(__file__), LEAF / "leaf.py", LEAF / "result.json",
               SOURCE / "control.xcnf.gz", SOURCE / "control_fixture.json",
               SOURCE / "control_result.json", SOURCE / "sage_fixture_result.json",
               leaf.ten.base.SOLVER)
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_BRANCH_HINT_PROFILE", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "point_law": "constructed ten-pair control point",
        "arms": ARMS, "branch_bits": json.loads((SOURCE / "control_result.json").read_text())["branch_bits"],
        "workers": 1, "cap_seconds_per_arm": CAP,
        "combined_rss_cap_bytes": RSS_CAP, "solver_flags": FLAGS,
        "sources": {str(path): sha(path) for path in sources},
        "raw_parent_sha256": leaf.prior.RAW_HASH,
    })


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_BRANCH_HINT_PROFILE"
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == leaf.prior.RAW_HASH
    circuit, common, branches, bits = bindings()
    assert bits == protocol["branch_bits"]
    regenerated = HERE / "regenerated.xcnf"
    circuit.write(regenerated)
    assert sha(regenerated) == leaf.prior.RAW_HASH
    regenerated.unlink()
    rows = []
    for name, arm in ARMS.items():
        path = HERE / f"{name}.xcnf"
        formula = leaf.variant(raw, arm_units(name, common, branches), path)
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
        row = {"arm": name, "branch_ids": arm["branch_ids"], "status": status,
               "terminal": terminals[-1] if terminals else None,
               "stop": stop, "exit_code": exit_code,
               "solver_wall_ns": elapsed, "peak_combined_rss_bytes": peak,
               "restart_rows": sum(x.startswith("c rst") for x in lines),
               "formula": formula, "archive_sha256": sha(archive),
               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath)}
        rows.append(row)
        print(json.dumps({key: row[key] for key in
                          ("arm", "status", "solver_wall_ns", "restart_rows")}), flush=True)
    save(HERE / "result.json", {"status": "COMPLETE_BRANCH_HINT_PROFILE",
                                "protocol_sha256": sha(HERE / "protocol.json"), "arms": rows})


def check_model(name, formula_path, log_path):
    lines = log_path.read_text(errors="replace").splitlines()
    assert [line for line in lines if line.startswith("s ")] == ["s SATISFIABLE"]
    assignment = {}
    for line in lines:
        if line.startswith("v "):
            for item in line.split()[1:]:
                literal = int(item)
                if literal:
                    assert abs(literal) not in assignment
                    assignment[abs(literal)] = literal > 0
    cnf = xor = 0
    with gzip.open(formula_path, "rt") as stream:
        header = stream.readline().split()
        assert header[:2] == ["p", "cnf"]
        variables, rows = map(int, header[2:])
        assert set(assignment) == set(range(1, variables + 1))
        for line in stream:
            parts = line.split()
            is_xor = parts[0] == "x"
            literals = list(map(int, parts[1 if is_xor else 0:-1]))
            assert parts[-1] == "0" and literals
            values = [assignment[abs(lit)] == (lit > 0) for lit in literals]
            if is_xor:
                assert sum(values) & 1, (name, xor)
                xor += 1
            else:
                assert any(values), (name, cnf)
                cnf += 1
    assert cnf + xor == rows and xor == 81064
    return {"arm": name, "variables": variables, "cnf_rows": cnf, "xor_rows": xor}


def verify():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert sha(HERE / "protocol.json") == result["protocol_sha256"]
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert hashlib.sha256(raw).hexdigest() == leaf.prior.RAW_HASH
    _, common, branches, bits = bindings()
    assert bits == protocol["branch_bits"]
    models = []
    for (name, arm), row in zip(ARMS.items(), result["arms"]):
        assert row["arm"] == name and row["branch_ids"] == list(arm["branch_ids"])
        path = HERE / f"{name}.xcnf"
        assert leaf.variant(raw, arm_units(name, common, branches), path) == row["formula"]
        archive = HERE / f"{name}.xcnf.gz"
        with gzip.open(archive, "rb") as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == row["formula"]["sha256"]
        path.unlink()
        outpath, errpath = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
        assert sha(outpath) == row["stdout_sha256"] and sha(errpath) == row["stderr_sha256"]
        lines = outpath.read_text(errors="replace").splitlines()
        assert sum(x.startswith("c rst") for x in lines) == row["restart_rows"]
        assert row["peak_combined_rss_bytes"] < RSS_CAP
        if row["status"] == "SAT":
            models.append(check_model(name, archive, outpath))
        else:
            assert row["status"] == "BOUNDED_UNKNOWN"
    save(HERE / "audit_result.json", {
        "status": "PASS_BRANCH_HINT_ARCHIVED_FORMULA_AND_MODEL_AUDIT",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "result_sha256": sha(HERE / "result.json"), "models": models})
    print("PASS_N131_TENPAIR_BRANCH_HINT_PROFILE", len(ARMS), len(models))


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
