#!/usr/bin/env sage -python
"""Independent Sage replay of all target-conjugate terminal residuals."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / "n131_w18_terminal4_20261012"
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
OLD = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    pool = json.loads((PARENT / "pool.json").read_text())
    parent_audit = json.loads((PARENT / "sage_audit_result.json").read_text())
    target = json.loads((OLD / "target_preimages.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert parent_audit["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL4_FIBERS"
    assert protocol["source_sha256"]["support"] == sha(SUPPORT)
    assert protocol["source_sha256"]["parent_pool.json"] == sha(PARENT / "pool.json")
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == target["public_target"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(integer):
        return field(ring([(int(integer) >> bit) & 1 for bit in range(131)]))

    def enc(value):
        return sum(int(bit) << bit_index
                   for bit_index, bit in enumerate(value.polynomial().list()))

    def point(pair):
        return curve([dec(pair[0]), dec(pair[1])])

    def xy(value):
        return [enc(value[0]), enc(value[1])]

    def tau(value):
        return curve([value[0]**2, value[1]**2])

    def coordinate(mask):
        return sum((field(t**(bit+1)) for bit in range(18) if mask >> bit & 1),
                   field.zero())

    def halftrace(value):
        result, power = field.zero(), value
        for _ in range(66):
            result += power
            power = power**4
        assert result**2 + result == value
        return result

    raw = point(target["preimages"][0]["point"])
    public = point(target["public_target"])
    assert 4 * raw == public and R * public == curve(0)
    source_table = [tuple(map(int, line.split())) for line in SUPPORT.read_text().splitlines()]
    assert len(source_table) == 131307
    columns = {column for _, column in source_table}
    assert len(columns) == 131068
    first_mask = source_table[0][0]
    u = halftrace(coordinate(first_mask))
    x = 1 + 1/u
    source_point = curve.lift_x(x, all=True)[0]
    subgroup_point = 4 * source_point
    assert subgroup_point != curve(0) and R * subgroup_point == curve(0)
    ring_r = PolynomialRing(GF(R), "L")
    L = ring_r.gen()
    roots = [int(root) for root, _ in (L**2 + L + 2).roots()]
    eigenvalues = [value for value in roots if value * subgroup_point == tau(subgroup_point)]
    assert len(eigenvalues) == 1
    lam = eigenvalues[0]
    assert lam != 1 and pow(lam, 131, R) == 1
    assert -1 % R not in {pow(lam, exponent, R) for exponent in range(131)}
    orbit_points = []
    current = subgroup_point
    for _ in range(131):
        orbit_points.append(current)
        current = tau(current)
    assert current == subgroup_point and len(set(orbit_points)) == 131
    assert len(set(orbit_points + [-value for value in orbit_points])) == 262
    assert protocol["source_geometry"]["full_signed_frobenius_base_size"] == 2 * 131 * len(columns)
    terminal = []
    for row in pool["states"]:
        lifts = []
        for mask in row["masks"]:
            u = halftrace(coordinate(mask))
            x = 1 + 1/u
            lifts.append(curve.lift_x(x, all=True))
        options = set()
        for left, right in itertools.product(*lifts):
            source_sum = left + right
            rotated = source_sum
            for _ in range(128):
                rotated = tau(rotated)
            options.add(rotated)
        assert len(options) == 4
        state = point(row["rotated_raw_point"])
        assert state in options
        terminal.append(state)
    assert len(set(terminal)) == 4
    rows, orbit_public = [], []
    current_raw, current_public = raw, public
    for rotation in range(131):
        assert 4 * current_raw == current_public
        assert current_public == pow(lam, rotation, R) * public
        orbit_public.append(current_public)
        for state_index, state in enumerate(terminal):
            residual = current_raw - state
            assert residual != curve(0) and residual[0] not in (0, 1)
            rows.append({"target_rotation": rotation,
                         "terminal_state_index": state_index,
                         "point": xy(residual),
                         "standard_reciprocal": enc(1/residual[0])})
        current_raw, current_public = tau(current_raw), tau(current_public)
    assert current_raw == raw and current_public == public
    assert len(set(orbit_public)) == 131 and len(rows) == 524
    assert len({row["standard_reciprocal"] for row in rows}) == 524
    result = {"status": "PASS_INDEPENDENT_SAGE_524_FROBENIUS_RESIDUALS",
              "curve_id": protocol["curve_id"],
              "workload_id": protocol["workload_id"],
              "target_orbit_size": len(orbit_public),
              "terminal_states": len(terminal),
              "residuals": rows,
              "folded_columns": len(columns),
              "full_signed_frobenius_base_size": 2 * 131 * len(columns),
              "frobenius_eigenvalue_mod_r": str(lam),
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "query": sha(HERE / "query_result.json"),
                                "pool": sha(PARENT / "pool.json"),
                                "support": sha(SUPPORT),
                                "parent_sage_audit": sha(PARENT / "sage_audit_result.json"),
                                "runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_residuals.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], len(rows))


if __name__ == "__main__":
    main()
