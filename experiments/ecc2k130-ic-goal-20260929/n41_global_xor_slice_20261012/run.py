"""Nested global XOR slices of the exact unpinned N41 public circuit."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
sys.path.insert(0, str(SOURCE))
import fourpair_v2  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, obj):
    with (HERE / name).open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def parity(value):
    return bin(value).count("1") & 1


def rank_add(basis, row):
    value = row
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = value
            return True
        value ^= basis[pivot]
    return False


def plan():
    fixture = json.loads((SOURCE / "n41_diagonal/control_fixture.json").read_text())
    target = fixture["target_reciprocal"]
    source_hash = sha(SOURCE / "fourpair_v2.py")
    rows, basis, counter = [], {}, 0
    while len(rows) < 11:
        material = f"n41-global-source-xor|{source_hash}|{target}|{counter}".encode()
        row = int.from_bytes(hashlib.sha256(material).digest()[:8], "little")
        counter += 1
        if any(((row >> (8*slot)) & 255) == 0 for slot in range(4)):
            continue
        if not 18 <= bin(row).count("1") <= 46 or not rank_add(basis, row):
            continue
        rows.append(row)
    masks = [mask for pair in fixture["masks"] for mask in pair]
    witness = sum(mask << (8*i) for i, mask in enumerate(masks))
    control = [parity(row & witness) for row in rows]
    ordinary = [hashlib.sha256(f"ordinary|{target}|{source_hash}|{i}".encode()).digest()[0] & 1
                for i in range(len(rows))]
    save("panel.json", {"status": "FROZEN_GLOBAL_XOR_ROWS", "rows": rows,
                        "rank": len(basis), "witness_parities": control,
                        "ordinary_parities": ordinary,
                        "cases": [{"name": "control8", "bits": control[:8], "cap_seconds": 60},
                                  {"name": "ordinary8", "bits": ordinary[:8], "cap_seconds": 150},
                                  {"name": "ordinary11", "bits": ordinary, "cap_seconds": 150}],
                        "selection": "SHA-256 rows; ordinary RHS from target and source only",
                        "target_reciprocal": target,
                        "positive_fixture_sha256": sha(SOURCE / "n41_diagonal/control_fixture.json")})


def freeze():
    paths = [Path(__file__), HERE / "panel.json", SOURCE / "fourpair_v2.py",
             SOURCE / "n41_diagonal/control_fixture.json",
             GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
             GOAL / "n41_basis_aware_quartic_20261011/sparse.py",
             GOAL.parent / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py", SOLVER]
    save("protocol.json", {"status": "FROZEN_BEFORE_GLOBAL_XOR_SLICE_PANEL",
                           "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
                           "workers": 1, "rss_cap_bytes": 4*1024**3,
                           "sources": {str(path): sha(path) for path in paths}})


def build(name):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    panel = json.loads((HERE / "panel.json").read_text())
    case = next(row for row in panel["cases"] if row["name"] == name)
    fixture = json.loads((SOURCE / "n41_diagonal/control_fixture.json").read_text())
    start = time.monotonic_ns()
    circuit, wires, meta = fourpair_v2.build("n41", panel["target_reciprocal"])
    masks = [wire for bits in wires["masks"] for wire in bits]
    assert len(masks) == 64
    for row, rhs in zip(panel["rows"], case["bits"]):
        literals = [masks[i] for i in range(64) if row >> i & 1]
        assert literals
        if rhs == 0:
            literals[0] = -literals[0]
        circuit.xors.append("x " + " ".join(map(str, literals)) + " 0")
    check = None
    if name == "control8":
        field, _, rotations = fourpair_v2.field_config("n41")
        check = fourpair_v2.check_assignment(circuit, wires, fixture, field, rotations)
    formula = HERE / f"{name}.xcnf"
    circuit.write(formula)
    save(f"{name}_build.json", {"status": "PASS_EXACT_GLOBAL_XOR_FORMULA",
         "name": name, "variables": circuit.next_var - 1,
         "cnf_clauses": len(circuit.clauses), "xor_rows": len(circuit.xors),
         "source_xor_rows": len(case["bits"]), "mask_wires": wires["masks"],
         "pair_output_wires": wires["pair_outputs"], "middle_wires": wires["middle"],
         "positive_assignment_check": check, "source_meta": meta,
         "formula_sha256": sha(formula), "formula_bytes": formula.stat().st_size,
         "build_ns": time.monotonic_ns() - start,
         "protocol_sha256": sha(HERE / "protocol.json")})
    print("BUILT", name, circuit.next_var - 1, flush=True)


def query(name):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    panel = json.loads((HERE / "panel.json").read_text())
    case = next(row for row in panel["cases"] if row["name"] == name)
    built = json.loads((HERE / f"{name}_build.json").read_text())
    formula = HERE / f"{name}.xcnf"
    assert sha(formula) == built["formula_sha256"]
    cap = case["cap_seconds"]
    flags = ["--threads=1", f"--maxtime={cap-5}", "--zero-exit-status", "--verb=1", "--printsol=1"]
    stdout, stderr = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
    start, peak, stop = time.monotonic_ns(), 0, None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *flags, str(formula)], stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, proc.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            if time.monotonic_ns()-start > cap*10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN" if stop or terminal in (None, "s INDETERMINATE") else
              "PRODUCER_FAILURE")
    save(f"{name}_result.json", {"status": status, "terminal": terminal,
         "stop_reason": stop, "exit_code": code, "wall_ns": time.monotonic_ns()-start,
         "peak_solver_rss_bytes": peak,
         "restart_rows": sum(line.startswith("c rst") for line in lines),
         "solver_flags": flags, "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
         "build_sha256": sha(HERE / f"{name}_build.json"),
         "protocol_sha256": sha(HERE / "protocol.json")})
    print("RESULT", name, status, flush=True)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "plan": plan()
    elif action == "freeze": freeze()
    elif action == "build": build(sys.argv[2])
    elif action == "query": query(sys.argv[2])
    else: raise ValueError(action)
