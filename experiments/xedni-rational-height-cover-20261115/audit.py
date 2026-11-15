"""Independently audit immutable hashes and the integer cover count."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def check_receipt(version, source, runtime):
    suffix = "" if version == 1 else "-v2"
    result = json.loads((HERE / f"result{suffix}.json").read_text())
    protocol = f"protocol{suffix}.json"
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(protocol)
    assert result["source_sha256"] == sha(source)
    assert result["sage_runtime_sha256"] == sha(runtime)
    assert (HERE / f"run{suffix}.stderr").stat().st_size == 0
    return result


def main():
    old = check_receipt(1, "run.py", "sage-runtime-info.json")
    new = check_receipt(2, "run_v2.py", "sage-runtime-info-v2.json")
    spec = json.loads((HERE / "protocol-v2.json").read_text())
    multipliers = spec["sample"]["lifted_point_multipliers"]
    L = spec["sample"]["coefficient_radius"]
    bound = L * sum(map(abs, multipliers))
    centers = set(range(-bound, bound + 1))
    values = [sum(a * m for a, m in zip(coeff, multipliers))
              for coeff in itertools.product(range(-L, L + 1), repeat=len(multipliers))]
    assert len(centers) == new["center_count"] == 13
    assert len(values) == new["coefficient_box_count"] == 27
    assert set(values) == centers
    assert len(set(values)) == old["distinct_rational_sum_count"] == new["distinct_sum_count"]
    assert sum(a * m for a, m in zip(spec["sample"]["known_relation"], multipliers)) == 0
    assert old["canonical_height_P"] == new["canonical_height_P"]
    assert new["covered_sum_count"] == new["reduction_checks"] == len(values)
    print("PASS: receipt hashes, empty stderr, precomputed center interval, exact cube, relation, height and reduction counts")


if __name__ == "__main__":
    main()
