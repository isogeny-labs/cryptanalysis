"""Independent Sage group and recursive-OBDD replay for one W20 subcube."""
import hashlib
import json
import time
from pathlib import Path

import psutil
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w20_sevenpair_gate_20261010" / "support_w20.tsv"
COUNT = ROOT / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recursive_bdd(values, bit_count):
    """High-bit-first recursion; invalid codes are don't-cares."""
    unique = {}

    def visit(row, bit):
        known = [v for v in row if v is not None]
        if not known:
            return None
        if all(v == known[0] for v in known):
            return known[0]
        assert bit >= 0
        half = len(row) // 2
        low, high = visit(row[:half], bit - 1), visit(row[half:], bit - 1)
        if low is None:
            return high
        if high is None or low == high:
            return low
        key = (bit, low, high)
        if key not in unique:
            unique[key] = len(unique) + 2
        return unique[key]

    roots = [visit([None if value is None else value >> outbit & 1
                    for value in values], bit_count - 1)
             for outbit in range(131)]
    return len(unique), len(set(roots)), sum(x is None for x in roots)


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    original = json.loads((HERE / "result.json").read_text())
    start = time.monotonic_ns()
    process = psutil.Process()
    rows = {int(mask): int(column) for mask, column, _shift
            in (line.split() for line in SUPPORT.read_text().splitlines())}
    seed = json.loads(COUNT.read_text())["selected_seed_mask"]
    assert seed == 898618
    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131 + t**13 + t**2 + t + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    basis = [field(t**(i+1)) for i in range(20)]
    zero = field.zero()
    sx = sum((basis[i] for i in range(20) if seed >> i & 1), zero)

    def coord(mask):
        return sum((basis[i] for i in range(20) if mask >> i & 1), zero)

    def ht(value):
        acc, term = zero, value
        for _ in range(66):
            acc += term
            term = term**4
        assert acc**2 + acc == value
        return acc

    def integer(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    h2 = ht(sx)**2
    coeff = 1 + h2
    assert coeff
    values = []
    direct_checked = 0
    group_sample = set(protocol["group_sample_codes"])
    for code in range(1 << 14):
        if code not in rows or code ^ seed not in rows or rows[code] == rows[code ^ seed]:
            values.append(None)
            continue
        p = coord(code) * coord(code ^ seed)
        delta = p / coeff
        v = ht(h2 * coeff / (p**2))
        roots = (v*delta, (v+1)*delta)
        assert roots[0] != roots[1]
        assert all(coeff*a**2 + p*a + h2 == 0 for a in roots)
        raw = integer(roots[0])
        canonical = min(map(integer, roots))
        values.append((raw, canonical))
        if code in group_sample:
            xa, xb = coord(code), coord(code ^ seed)
            def source_points(w):
                u = ht(w)
                assert u and 1/u
                return curve.lift_x(1 + 1/u, all=True)
            observed = set()
            for left in source_points(xa):
                for right in source_points(xb):
                    combined = left + right
                    assert combined != curve(0) and combined[0] != 0
                    observed.add(integer(1/combined[0]))
            assert observed == set(map(integer, roots))
            direct_checked += 1
        if code % 512 == 0:
            assert process.memory_info().rss < protocol["rss_cap_bytes"]
            assert time.monotonic_ns() - start < protocol["wall_cap_seconds"]*10**9
    assert direct_checked == len(group_sample)
    expected = next(row for row in original["records"]
                    if row["prefix_m14"] == 0 and row["bit_count"] == 14)
    assert len([x for x in values if x is not None]) == expected["valid_codes"]
    raw = [None if x is None else x[0] for x in values]
    canonical = [None if x is None else x[1] for x in values]
    raw_count = recursive_bdd(raw, 14)
    canonical_count = recursive_bdd(canonical, 14)
    assert raw_count == (expected["halftrace_root_shared_nodes"],
                         expected["halftrace_distinct_output_roots"],
                         expected["undefined_output_bits"][0])
    assert canonical_count == (expected["canonical_root_shared_nodes"],
                               expected["canonical_distinct_output_roots"],
                               expected["undefined_output_bits"][1])
    result = {"status": "PASS_INDEPENDENT_SAGE_W20_ROOT_BDD_SUBCUBE",
              "candidate_id": None, "prefix_m14": 0, "bit_count": 14,
              "valid_codes": expected["valid_codes"],
              "direct_group_codes_checked": direct_checked,
              "halftrace_bdd_nodes": raw_count[0],
              "canonical_bdd_nodes": canonical_count[0],
              "peak_process_rss_sample_bytes": process.memory_info().rss,
              "wall_ns": time.monotonic_ns() - start,
              "protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(result["status"], expected["valid_codes"], direct_checked, flush=True)


if __name__ == "__main__":
    main()
