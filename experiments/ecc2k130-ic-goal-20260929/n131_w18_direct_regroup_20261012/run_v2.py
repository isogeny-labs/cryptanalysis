"""Freeze and check a direct first/terminal W18 regrouped circuit."""

import argparse
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
GROUP = ROOT / "n131_fixed_seed_halftrace_cubic_20261011/verify.py"
FIXTURE = BASE / "control_fixture.json"
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
RUNTIME = HERE / "sage_runtime_info.json"
sys.path[:0] = [str(HERE), str(BASE), str(GROUP.parent)]
import circuit_v2 as operator  # noqa: E402
base = operator.base
spec = importlib.util.spec_from_file_location("sevenpair_group", GROUP)
group = importlib.util.module_from_spec(spec)
spec.loader.exec_module(group)

RSS_CAP = 4 * 1024**3
PARENT_CAP = 600


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, record):
    with (HERE / name).open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write("\n")


def sources():
    return {"runner": HERE / "run_v2.py", "circuit": HERE / "circuit_v2.py",
            "base": BASE / "run.py", "fixture": FIXTURE,
            "group": GROUP, "pool": POOL,
            "pair": base.OLD / "fixed_pair_circuit.py",
            "support": base.SUPPORT,
            "sparse": ROOT / "n41_basis_aware_quartic_20261011/sparse.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
            "circuit_sat": ROOT.parent / "koblitz-s5-invariant-20260924/circuit_sat.py",
            "target": base.OLD / "target_preimages.json",
            "runtime": RUNTIME, "solver": base.SOLVER.resolve()}


def rotated_pair(item):
    left, right = item["masks"]
    raw = group.point_add(group.point_options(left)[0],
                          group.point_options(right)[0])
    assert raw is not None
    exponent = item["rotation"]
    return (group.frobenius(raw[0], exponent),
            group.frobenius(raw[1], exponent)), raw


def constructed():
    fixture = json.loads(FIXTURE.read_text())
    selected = fixture["selected"]
    assert len(selected) == 9
    pairs, unrotated = zip(*(rotated_pair(item) for item in selected))
    block = group.point_add(pairs[0], pairs[8])
    assert block is not None and block[0]
    running = None
    middle = []
    for point in pairs[1:8]:
        running = group.point_add(running, point)
        middle.append(running)
    seven_sum = running
    target = group.point_add(seven_sum, block)
    assert target is not None and target[0]
    return {"selected": selected, "pairs": pairs,
            "unrotated": unrotated, "block": block,
            "middle": middle[1:], "seven_sum": seven_sum,
            "target": target}


def freeze():
    assert RUNTIME.is_file()
    target = base.target_record()
    _, bdd_root, bdd_nodes = base.source_domain()
    assert bdd_root >= 2 and len(bdd_nodes) == 13093
    witness = constructed()
    pool = json.loads(POOL.read_text())
    assert pool["states"][0]["code"] == 10
    assert witness["selected"][8]["masks"] == pool["states"][0]["masks"]
    save("protocol_v2.json", {
        "status": "FROZEN_SEVENPAIR_DIRECT_REGROUP_BEFORE_BUILD",
        "candidate_id": None, "curve_id": target["curve_id"],
        "workload_id": target["workload_id"],
        "public_target": target["public_target"],
        "raw_preimage_index": 0,
        "constructed_target_raw": list(witness["target"]),
        "constructed_block_raw": list(witness["block"]),
        "terminal_codes": operator.constants()[0],
        "first_rotation": 0, "free_rotations": operator.FREE_ROTATIONS,
        "terminal_rotation": operator.TERMINAL_ROTATION,
        "worker_count": 1, "parent_cap_seconds": PARENT_CAP,
        "rss_cap_bytes": RSS_CAP,
        "source_sha256": {name: sha(path) for name, path in sources().items()},
    })
    print("FROZEN_SEVENPAIR_DIRECT_REGROUP_BEFORE_BUILD", flush=True)


def protocol():
    record = json.loads((HERE / "protocol_v2.json").read_text())
    assert record["status"] == "FROZEN_SEVENPAIR_DIRECT_REGROUP_BEFORE_BUILD"
    assert record["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert record["rss_cap_bytes"] == RSS_CAP and record["parent_cap_seconds"] == PARENT_CAP
    return record


def bind(initial, bits, value):
    initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})


def control():
    frozen = protocol()
    witness = constructed()
    assert list(witness["target"]) == frozen["constructed_target_raw"]
    assert list(witness["block"]) == frozen["constructed_block_raw"]
    target_a = group.inverse(witness["target"][0])
    _, bdd_root, bdd_nodes = base.source_domain()
    start = time.monotonic_ns()
    circuit, wires = operator.build(target_a, bdd_root, bdd_nodes)
    built = time.monotonic_ns()
    assert (built-start) < PARENT_CAP*10**9
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < RSS_CAP
    formula = HERE / "control_v2.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    selected = witness["selected"]
    bind(initial, wires["first_code"], base.pair.selector_code(selected[0]["masks"][0]))
    first_a = group.inverse(witness["unrotated"][0][0])
    terminal_a = group.inverse(witness["pairs"][8][0])
    bind(initial, wires["first_output"], first_a)
    bind(initial, wires["terminal_output"], terminal_a)
    codes = wires["terminal_codes"]
    assert codes[0] == base.pair.selector_code(selected[8]["masks"][0])
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == 0)
    h2 = base.pair.gf_square(base.pair.gf_half_trace(base.pair.coordinate(base.pair.SEED)))
    k = 1 ^ h2
    terminal_h2 = base.pair.gf_frobenius(h2, 128)
    ell = 1 ^ terminal_h2
    p = base.pair.product_from_code(codes[0])
    q = base.pair.gf_frobenius(p, 128)
    first_product = selected[0]["product_p"]
    assert base.pair.gf_mul(k, base.pair.gf_square(first_a)) ^ base.pair.gf_mul(first_product, first_a) ^ h2 == 0
    assert base.pair.gf_mul(ell, base.pair.gf_square(terminal_a)) ^ base.pair.gf_mul(q, terminal_a) ^ terminal_h2 == 0
    rotated_a = []
    for index, (item, raw) in enumerate(zip(selected[1:8], witness["unrotated"][1:8])):
        code = base.pair.selector_code(item["masks"][0])
        bind(initial, wires["selectors"][index], code)
        value = group.inverse(raw[0])
        bind(initial, wires["pair_outputs"][index], value)
        product = base.pair.product_from_code(code)
        assert base.pair.gf_mul(k, base.pair.gf_square(value)) ^ base.pair.gf_mul(product, value) ^ h2 == 0
        rotated_a.append(group.inverse(witness["pairs"][index+1][0]))
    middle_a = [group.inverse(point[0]) for point in witness["middle"]]
    assert len(middle_a) == 6
    for bits, value in zip(wires["middle"], middle_a):
        bind(initial, bits, value)
    block_a = group.inverse(witness["block"][0])
    bind(initial, wires["block"], block_a)
    assert base.pair.gf_mul(block_a, witness["block"][0]) == 1
    running = rotated_a[0]
    branch_rows = []
    for index in range(1, 7):
        output = middle_a[index-1]
        total = running ^ rotated_a[index] ^ output
        branch = base.pair.gf_mul(base.pair.gf_mul(running, rotated_a[index]), output) ^ base.halftrace(base.pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index-1]] = branch
        branch_rows.append(branch)
        running = output
    total = running ^ block_a ^ target_a
    branch = base.pair.gf_mul(base.pair.gf_mul(running, block_a), target_a) ^ base.halftrace(base.pair.gf_square(total))
    assert branch in (0, 1)
    initial[wires["branches"][6]] = branch
    branch_rows.append(branch)
    total = first_a ^ terminal_a ^ block_a
    block_branch = base.pair.gf_mul(base.pair.gf_mul(first_a, terminal_a), block_a) ^ base.halftrace(base.pair.gf_square(total))
    assert block_branch in (0, 1)
    initial[wires["branches"][7]] = block_branch
    branch_rows.append(block_branch)
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result_v2.json", {
        "status": "PASS_SEVENPAIR_DIRECT_REGROUP_CONSTRUCTED_WITNESS",
        "candidate_id": None, "constructed_target_raw": list(witness["target"]),
        "constructed_block_raw": list(witness["block"]),
        "first_product": selected[0]["product_p"],
        "terminal_code": codes[0], "branch_bits": branch_rows,
        "primary_variables": len(initial), "assignment_check": checked,
        "formula": base.profile(circuit, formula, (built-start)/1e9,
                                (written-built)/1e9),
        "protocol_sha256": sha(HERE / "protocol_v2.json"),
    })
    print("PASS_SEVENPAIR_DIRECT_REGROUP_CONSTRUCTED_WITNESS", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control"))
    args = parser.parse_args()
    globals()[args.mode]()
