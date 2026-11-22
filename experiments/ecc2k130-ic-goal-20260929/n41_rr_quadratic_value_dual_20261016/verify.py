"""Independent replay of all quadratic certificates and the positive control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_rr_pairwise_certificate_20261017"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
freeze = json.loads((HERE / "verification_protocol.json").read_text())
for path, digest in freeze["sources"].items():
    assert sha(path) == digest, path
assert sha(HERE / "verify.py") == freeze["verifier_sha256"]
out = json.loads((HERE / "result.json").read_text())
original = json.loads((PARENT / "result.json").read_text())["charts"]
other = json.loads((PARENT / "fullroot_result.json").read_text())["rows"]
assert out["feature_count"] == 861 and out["code_count"] == 35
assert len(original) == len(other) == len(out["rows"]) == 35

def evaluate_an_fresh(coeffs, assignment):
    return_value = 0
    for support, coefficient in enumerate(coeffs):
        if support & assignment == support:
            return_value ^= coefficient
    return return_value

def evaluate_quadratic(weight, value):
    bits = [(value >> i) & 1 for i in range(41)]
    answer = sum(bits[i] * ((weight >> i) & 1) for i in range(41)) & 1
    position = 41
    for i in range(41):
        for j in range(i + 1, 41):
            answer ^= bits[i] & bits[j] & ((weight >> position) & 1)
            position += 1
    assert position == 861
    return answer

def low_rank(values):
    basis = {}
    for value in values:
        while value:
            pivot = (value & -value).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)

def low_consistent(rows):
    """Independent low-pivot elimination on (feature, constant-one) rows."""
    basis = {}
    for row in rows:
        label = 1
        while row:
            pivot = (row & -row).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (row, label)
                break
            saved, saved_label = basis[pivot]
            row ^= saved
            label ^= saved_label
        else:
            if label:
                return False
    return True

def monomial_vector(value):
    bits = [(value >> i) & 1 for i in range(41)]
    vector = sum(bit << i for i, bit in enumerate(bits))
    position = 41
    for i in range(41):
        for j in range(i + 1, 41):
            vector |= (bits[i] & bits[j]) << position
            position += 1
    return vector

by_code = {}
for a, b, row in zip(original, other, out["rows"]):
    assert a["mask"] == b["mask"] == row["mask"]
    panels = [a["coefficients"], b["root1_coefficients"]]
    values = [[evaluate_an_fresh(panel, sign) for sign in range(64)]
              for panel in panels]
    assert row["zero_states"] == [[root, sign] for root in range(2)
                                  for sign in range(64) if values[root][sign] == 0]
    assert a["zero_signs"] == [sign for sign, value in enumerate(values[0]) if value == 0]
    assert b["root1_zero_signs"] == [sign for sign, value in enumerate(values[1]) if value == 0]
    flat = values[0] + values[1]
    by_code[row["mask"]] = flat
    if row["single_code_certifiable"]:
        witness = int(row["certificate_hex"], 16)
        assert not row["zero_states"]
        assert all(evaluate_quadratic(witness, value) == 1 for value in flat)
        assert low_rank([monomial_vector(value) for value in flat]) == row["single_code_rank"]
    else:
        assert row["zero_states"] and row["certificate_hex"] is None

assert out["single_code_certifiable_count"] == 34
assert [row["mask"] for row in out["rows"] if row["zero_states"]] == [6]
assert out["rows"][3]["zero_states"] == [[1, 15]]
greedy = out["greedy_certified_codes"]
assert greedy == [2, 3, 5, 7, 16, 18]
assert len(set(greedy)) == len(greedy)
weight = int(out["greedy_certificate_hex"], 16)
all_values = [value for mask in greedy for value in by_code[mask]]
assert len(all_values) == 768
assert all(evaluate_quadratic(weight, value) == 1 for value in all_values)
assert low_rank([monomial_vector(value) for value in all_values]) == out["greedy_rank"] == 768
assert len(out["greedy_extension_checks"]) == 29
for check in out["greedy_extension_checks"]:
    assert check["mask"] not in greedy
    assert check["can_extend_greedy_certificate"] is False
    extension_values = all_values + by_code[check["mask"]]
    assert not low_consistent([monomial_vector(value) for value in extension_values])
for bucket in out["prefix_buckets"]:
    depth = bucket["prefix_bits"]
    prefix = bucket["prefix"]
    masks = bucket["code_masks"]
    assert 0 <= depth <= 8
    assert masks == [mask for mask in by_code if mask >> (8 - depth) == prefix]
    bucket_values = [value for mask in masks for value in by_code[mask]]
    if bucket["certifiable"]:
        bucket_weight = int(bucket["certificate_hex"], 16)
        assert all(evaluate_quadratic(bucket_weight, value) == 1 for value in bucket_values)
        assert low_rank([monomial_vector(value) for value in bucket_values]) == bucket["rank_until_decision"]
    else:
        assert bucket["certificate_hex"] is None
        assert not low_consistent([monomial_vector(value) for value in bucket_values])
depth4 = [bucket for bucket in out["prefix_buckets"] if bucket["prefix_bits"] == 4]
assert len(depth4) == 8 and sum(bucket["certifiable"] for bucket in depth4) == 7
assert max(len(bucket["code_masks"]) for bucket in depth4 if bucket["certifiable"]) == 5
lean = (HERE / "lean.stdout").read_text()
assert "'QuadraticCertificate.certificate_excludes_zero' depends on axioms: [propext, Quot.sound]" in lean
assert "sorryAx" not in lean and not (HERE / "lean.stderr").read_text()

receipt = {"status": "PASS_N41_QUADRATIC_RR_VALUE_CERTIFICATES",
           "result_sha256": sha(HERE / "result.json"),
           "verification_protocol_sha256": sha(HERE / "verification_protocol.json"),
           "certified_complete_code_families": 6,
           "certified_four_bit_prefix_buckets": 7,
           "positive_control_mask": 6,
           "positive_control_root_sign": [1, 15]}
(HERE / "terminal.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(receipt["status"])
