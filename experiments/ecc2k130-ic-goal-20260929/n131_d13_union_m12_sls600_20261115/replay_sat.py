"""Independently replay a SAT model as twelve Sage curve points and one relation.

Run only after query_result.json reports SAT_PENDING_REPLAY. The XCNF is
checked first, followed by source membership, every reciprocal S3 link,
the selected cofactor lift, and the projected prime-subgroup relation.
"""

import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SCREEN = EXP / "n131_d13_union_arity_20261115"
GEOMETRY = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json"
VALID = EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004" / "workload.json"
RESULT = HERE / "replay_result.json"
N = 131
M = 12
DIM = 13


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def model_from_log(path, nvars):
    values = [None] * (nvars + 1)
    lines = Path(path).read_text(errors="replace").splitlines()
    assert "s SATISFIABLE" in lines
    for line in lines:
        if not line.startswith("v "):
            continue
        for token in line.split()[1:]:
            lit = int(token)
            if lit == 0:
                continue
            index = abs(lit)
            assert 1 <= index <= nvars
            bit = lit > 0
            assert values[index] is None or values[index] == bit
            values[index] = bit
    assert all(bit is not None for bit in values[1:])
    return values


def check_xcnf(path, values):
    with Path(path).open() as stream:
        header = next(stream).split()
        assert header[:2] == ["p", "cnf"]
        assert int(header[2]) == len(values) - 1
        expected_rows = int(header[3])
        clauses = xors = 0
        for line in stream:
            if line.startswith("c") or not line.strip():
                continue
            is_xor = line.startswith("x")
            literals = [int(token) for token in
                        (line[1:] if is_xor else line).split()]
            assert literals and literals[-1] == 0
            literals.pop()
            assert literals
            bits = [values[abs(lit)] == (lit > 0) for lit in literals]
            if is_xor:
                xors += 1
                assert sum(bits) & 1, ("xor", xors)
            else:
                clauses += 1
                assert any(bits), ("clause", clauses)
    assert clauses + xors == expected_rows
    return clauses, xors


def mask_from_values(values, start, width):
    return sum(int(values[start + bit]) << bit for bit in range(width))


def primary_values(values):
    cursor = 1
    leaves = []
    for _ in range(M):
        code = mask_from_values(values, cursor, DIM)
        cursor += DIM
        branch = mask_from_values(values, cursor, 1)
        cursor += 1
        phi = mask_from_values(values, cursor, N)
        cursor += N
        leaves.append((code, branch, phi))
    partials = []
    for _ in range(M - 2):
        partials.append(mask_from_values(values, cursor, N))
        cursor += N
    endpoint = mask_from_values(values, cursor, 2)
    return leaves, partials, endpoint


def sage_field():
    bitpoly = (1 << N) | (1 << 13) | (1 << 2) | (1 << 1) | 1
    ring = PolynomialRing(GF(2), "z")
    modulus = ring([bitpoly >> i & 1 for i in range(N + 1)])
    field = GF(2**N, name="z", modulus=modulus)
    zeta = field.multiplicative_generator() ** ((2**N - 1) // 263)
    basis = [zeta**i + zeta**(263 - i) for i in range(1, N + 1)]
    inverse = Matrix(GF(2), [b.list() for b in basis]).transpose().inverse()
    dual = [sum(int(bit) << j for j, bit in enumerate(row))
            for row in inverse.rows()]
    assert sum(basis, field(0)) == 1

    def decode(mask):
        result = field(0)
        bits = int(mask)
        while bits:
            low = bits & -bits
            result += basis[low.bit_length() - 1]
            bits ^= low
        return result

    def encode(value):
        polybits = sum(int(bit) << i for i, bit in enumerate(value.list()))
        return sum(((polybits & row).bit_count() & 1) << i
                   for i, row in enumerate(dual))

    return field, decode, encode


def chart(point, zero):
    if point == zero or point[0] == 1:
        return None
    return 1 / (point[0] + 1)


def main():
    assert not RESULT.exists()
    protocol = read(HERE / "query_protocol.json")
    query = read(HERE / "query_result.json")
    assert query["status"] == "SAT_PENDING_REPLAY"
    assert protocol["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert protocol["workload_id"] == "3c1992b7c92f"
    started = time.monotonic()
    screen = read(SCREEN / "result.json")
    values = model_from_log(HERE / "solver.stdout",
                            screen["rows"]["12"]["formula_counts"]["vars"])
    clauses, xors = check_xcnf(HERE / "ordinary.xcnf", values)
    assert clauses == screen["rows"]["12"]["formula_counts"]["clauses"]
    assert xors == screen["rows"]["12"]["formula_counts"]["xors"]
    leaves, partials, endpoint_index = primary_values(values)
    geometry = read(GEOMETRY)
    workload = read(OFFICIAL)
    basis_masks = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    valid = {int(code): int(mask) for code, mask in read(VALID)}
    field, decode, encode = sage_field()
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    lifts = geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]
    assert [int(x) for x in workload["targets"][0]] == [int(x) for x in lifts[0]["target_coordinates"]]
    endpoints = [curve(decode(int(item["target_coordinates"][0])),
                       decode(int(item["target_coordinates"][1]))) for item in lifts]
    source_points = []
    for position, (code, branch, phi_mask) in enumerate(leaves):
        assert code in valid and branch in (0, 1)
        mask = 0
        for bit, basis_mask in enumerate(basis_masks):
            if code >> bit & 1:
                mask ^= basis_mask
        assert mask == valid[code]
        source_phi = decode(mask) ** (2**position)
        assert source_phi != 0
        x = 1 / source_phi + 1
        choices = curve.lift_x(x, all=True)
        assert len(choices) == 2
        source = choices[0]
        point = source + curve(source[0]**2, source[1]**2) if branch else source
        assert chart(point, zero) is not None
        assert encode(chart(point, zero)) == phi_mask
        source_points.append(point)

    states = [(zero, [])]
    for position, point in enumerate(source_points):
        new = []
        for running, signs in states:
            for sign in (1, -1):
                trial = running + (point if sign == 1 else -point)
                if position < M - 1 and position >= 1:
                    coordinate = chart(trial, zero)
                    if coordinate is None or encode(coordinate) != partials[position - 1]:
                        continue
                new.append((trial, signs + [sign]))
        assert new, ("partial", position)
        states = new
    selected = endpoints[endpoint_index]
    assert encode(chart(selected, zero)) == int(lifts[endpoint_index]["phi_coordinate"])
    matches = [(running, signs) for running, signs in states if running == selected]
    assert matches, "no consistent signs reach selected cofactor lift"
    running, signs = matches[0]
    assert running == selected
    public = endpoints[0]
    order = int(screen["subgroup_order"])
    assert order * public == zero
    assert 4 * (running - public) == zero
    inverse_four = pow(4, -1, order)
    projected = [inverse_four * (4 * point) for point in source_points]
    assert all(order * point == zero for point in projected)
    relation = zero
    for sign, point in zip(signs, projected):
        relation += point if sign == 1 else -point
    assert relation == public
    receipt = {
        "kind": "n131_d13_union_m12_sls600_independent_sage_sat_replay_v1",
        "status": "PASS_SOURCE_BOUND_PROJECTED_RELATION",
        "query_protocol_sha256": sha(HERE / "query_protocol.json"),
        "query_result_sha256": sha(HERE / "query_result.json"),
        "replay_source_sha256": sha(__file__),
        "solver_stdout_sha256": sha(HERE / "solver.stdout"),
        "formula_sha256": sha(HERE / "ordinary.xcnf"),
        "checked_clauses": clauses, "checked_native_xors": xors,
        "leaf_codes": [item[0] for item in leaves],
        "leaf_branch_bits": [item[1] for item in leaves],
        "leaf_phi_masks": [item[2] for item in leaves],
        "signs": signs, "endpoint_index": endpoint_index,
        "checked_partial_sums": len(partials),
        "elapsed_seconds": time.monotonic() - started,
        "relation_boundary": "Projected subgroup points sum to the frozen public point; factor logs and scalar recovery are later gates.",
    }
    RESULT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "endpoint_index": endpoint_index,
                      "checked_clauses": clauses,
                      "checked_native_xors": xors}, sort_keys=True))


if __name__ == "__main__":
    main()
