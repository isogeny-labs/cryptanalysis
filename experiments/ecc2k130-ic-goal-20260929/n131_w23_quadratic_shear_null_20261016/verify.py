"""Independent replay of random-law, shear identities and low-pivot cutoffs."""
import hashlib
import json
from functools import reduce
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
freeze = json.loads((HERE / "verification_protocol.json").read_text())
for path, digest in freeze["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "verify.py") == freeze["verifier_sha256"]
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
archive = json.loads((HERE / "coefficients.json").read_text())
real = json.loads((HERE.parent / "n131_w23_rr_quadratic_capacity_20261016/certificate.json").read_text())
assert result["feature_count"] == 8646 and result["seeds"] == protocol["seeds"] == list(range(8))
assert len(archive) == len(result["controls"]) == 8
assert real["first_failure_index"] == 8642

quadratic = [mask for mask in range(64) if mask.bit_count() == 2]
cubic = [mask for mask in range(64) if mask.bit_count() == 3]
pivots = result["cubic_pivot_masks"]
assert len(pivots) == len(set(pivots)) == 6 and all(mask in cubic for mask in pivots)

def expected_random(seed, chart, mask):
    key = b"N131-W23-RR-SHEAR-NULL-V1|" + seed.to_bytes(1, "big") + chart.to_bytes(2, "big") + mask.to_bytes(1, "big")
    return int.from_bytes(hashlib.shake_256(key).digest(17), "little") & ((1 << 131) - 1)

def value_from_anf(coeff, sign):
    value = 0
    for support, coefficient in enumerate(coeff):
        if (support & sign) == support:
            value ^= coefficient
    return value

def feature_vector(value):
    active = [i for i in range(131) if value >> i & 1]
    vector = value
    for position, i in enumerate(active):
        prefix = 131 + (i * (261 - i)) // 2
        for j in active[position + 1:]:
            vector |= 1 << (prefix + j - i - 1)
    assert vector.bit_length() <= 8646
    return vector

checks = []
for seed, (block, control) in enumerate(zip(archive, result["controls"])):
    assert block["seed"] == control["seed"] == seed
    basis = {}
    row_index = 0
    failure = None
    zero_count = 0
    for expected_chart, chart_record in enumerate(block["charts"]):
        chart = chart_record["chart"]
        coeff = chart_record["coefficients"]
        assert chart == expected_chart
        assert len(coeff) == 64
        for mask, entry in enumerate(coeff):
            if mask.bit_count() > 3:
                assert entry == 0
            elif mask not in pivots and mask != quadratic[0]:
                assert entry == expected_random(seed, chart, mask)
        assert reduce(int.__xor__, (coeff[mask] for mask in quadratic), 0) == 0
        for excluded in range(6):
            assert reduce(int.__xor__,
                (coeff[mask] for mask in cubic if not mask >> excluded & 1), 0) == 0
        for sign in range(64):
            value = value_from_anf(coeff, sign)
            zero_count += value == 0
            vector = feature_vector(value)
            label = 1
            while vector:
                pivot = (vector & -vector).bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = (vector, label)
                    break
                saved, saved_label = basis[pivot]
                vector ^= saved
                label ^= saved_label
            else:
                if label:
                    failure = {"row_index": row_index, "code_ordinal": chart // 2,
                               "root": chart % 2, "sign": sign,
                               "rank_before_failure": len(basis)}
                    break
            row_index += 1
        if failure is not None:
            break
    assert failure == control["first_failure"]
    assert row_index == control["rows_inserted"] and len(basis) == control["rank"]
    assert zero_count == control["zero_values_through_stop"] == 0
    assert len(block["charts"]) == control["charts_generated"] == 136
    assert failure["code_ordinal"] == 67
    checks.append({"seed": seed, "first_failure_index": row_index,
                   "rank_before_failure": len(basis)})
    print(json.dumps(checks[-1], sort_keys=True), flush=True)

offsets = [item["first_failure_index"] - real["first_failure_index"] for item in checks]
assert offsets == [1, 3, 6, 7, 0, 7, 3, 5]
receipt = {"status": "PASS_N131_SHEAR_RANDOM_NULL_REPLAY",
           "controls": checks,
           "real_first_failure_index": real["first_failure_index"],
           "offsets_from_real": offsets,
           "result_sha256": sha(HERE / "result.json"),
           "coefficients_sha256": sha(HERE / "coefficients.json"),
           "verification_protocol_sha256": sha(HERE / "verification_protocol.json")}
(HERE / "terminal.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(receipt["status"])
