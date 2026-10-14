"""Exact W20 root-function BDD screen on frozen selector subcubes."""
import hashlib
import json
import time
from pathlib import Path

import psutil
from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w20_sevenpair_gate_20261010" / "support_w20.tsv"
COUNT = ROOT / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"
FIXTURE = ROOT / "n131_w20_sevenpair_gate_20261010" / "sage_audit_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bdd_nodes(roots, bit_count, output_bits=131):
    """Shared OBDD with undefined invalid codes as don't-cares."""
    unique = {}
    root_ids = []
    for outbit in range(output_bits):
        row = [None if value is None else (value >> outbit) & 1 for value in roots]
        for level in range(bit_count):
            next_row = []
            for index in range(0, len(row), 2):
                lo, hi = row[index], row[index + 1]
                if lo is None:
                    node = hi
                elif hi is None or lo == hi:
                    node = lo
                else:
                    key = (level, lo, hi)
                    node = unique.setdefault(key, len(unique) + 2)
                next_row.append(node)
            row = next_row
        assert len(row) == 1
        root_ids.append(row[0])
    return len(unique), len(set(root_ids)), len([x for x in root_ids if x is None])


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    start = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    count = json.loads(COUNT.read_text())
    seed = count["selected_seed_mask"]
    assert seed == 898618 and seed.bit_length() == 20
    columns = {}
    for line in SUPPORT.read_text().splitlines():
        mask, column, _shift = map(int, line.split())
        columns[mask] = column
    assert len(columns) == 524493
    valid = {code for code in range(1 << 19)
             if code in columns and code ^ seed in columns
             and columns[code] != columns[code ^ seed]}
    assert len(valid) == 132045
    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131 + t**13 + t**2 + t + 1)
    zero = field.zero()
    powers = [field(t**(bit+1)) for bit in range(20)]
    seed_x = sum((powers[bit] for bit in range(20) if seed >> bit & 1), zero)

    def halftrace(value):
        result, term = zero, value
        for _ in range(66):
            result += term
            term = term**4
        assert result**2 + result == value
        return result

    h = halftrace(seed_x)
    h2 = h**2
    k = 1 + h2
    assert k != 0

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    cache = {}
    def roots_for_code(code):
        if code not in cache:
            x = sum((powers[bit] for bit in range(19) if code >> bit & 1), zero)
            p = x * (x + seed_x)
            assert p != 0
            delta = p/k
            trace_arg = (h2*k)/(p**2)
            root = delta * halftrace(trace_arg)
            other = root + delta
            assert root != other
            assert k*root**2 + p*root + h2 == 0
            assert k*other**2 + p*other + h2 == 0
            raw = encode(root)
            alternative = encode(other)
            cache[code] = (raw, min(raw, alternative))
        return cache[code]

    fixture = json.loads(FIXTURE.read_text())
    selected = fixture["selected"][0]
    witness = min(selected["masks"])
    assert witness in valid
    actual_root, canonical_root = roots_for_code(witness)
    assert actual_root and canonical_root
    prefixes = protocol["prefixes_m14"]
    sizes = protocol["subcube_bit_counts"]
    records = []
    for prefix in prefixes:
        for bits in sizes:
            peak = max(peak, process.memory_info().rss)
            assert peak < protocol["rss_cap_bytes"]
            assert time.monotonic_ns() - start < protocol["wall_cap_seconds"] * 10**9
            base = prefix << 14
            values = [roots_for_code(code) if code in valid else None
                      for code in range(base, base + (1 << bits))]
            accepted = sum(value is not None for value in values)
            raw = [None if x is None else x[0] for x in values]
            canonical = [None if x is None else x[1] for x in values]
            raw_nodes, raw_roots, raw_undefined = bdd_nodes(raw, bits)
            canonical_nodes, canonical_roots, canonical_undefined = bdd_nodes(canonical, bits)
            records.append({"prefix_m14": prefix, "bit_count": bits,
                            "valid_codes": accepted,
                            "halftrace_root_shared_nodes": raw_nodes,
                            "canonical_root_shared_nodes": canonical_nodes,
                            "halftrace_distinct_output_roots": raw_roots,
                            "canonical_distinct_output_roots": canonical_roots,
                            "undefined_output_bits": [raw_undefined, canonical_undefined]})
    result = {"status": "PASS_W20_ROOT_FUNCTION_SUBCUBE_BDD_SCREEN",
              "candidate_id": None,
              "valid_codes_full_domain": len(valid),
              "root_codes_computed": len(cache),
              "witness_code": witness,
              "witness_halftrace_root": actual_root,
              "witness_canonical_root": canonical_root,
              "records": records,
              "peak_process_rss_sample_bytes": peak,
              "wall_ns": time.monotonic_ns() - start,
              "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "result.json").open("x") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(result["status"], len(cache), len(records), flush=True)


if __name__ == "__main__":
    main()
