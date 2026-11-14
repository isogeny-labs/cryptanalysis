#!/usr/bin/env python3
"""Independent finite verification of the supplied blind arithmetic claims.

This script reads only the supplied blind input, for its SHA-256 digest.
Every arithmetic assertion is defined independently below; no producer code,
proof, result, repository metadata, or sibling output is consumed.
"""

import hashlib
import json


INPUT = "/var/tmp/cryptanalysis-p997-review-20261107/reports/2026-11-07-hecke-p997-review/blind-input.md"
OUTPUT = "/var/tmp/p997-blind-review-output/verification.json"


def sum_triples(total, cap=None):
    for a in range(total + 1):
        for b in range(total - a + 1):
            c = total - a - b
            if cap is None or max(a, b, c) <= cap:
                yield (a, b, c)


def nat_sub(a, b):
    return max(a - b, 0)


with open(INPUT, "rb") as input_file:
    source_bytes = input_file.read()

claim_1_domain = list(sum_triples(72, cap=24))
claim_1_failures = [t for t in claim_1_domain if t != (24, 24, 24)]
claim_2_domain = list(sum_triples(12))
claim_2_failures = [t for t in claim_2_domain if not any(0 < x < 24 for x in t)]
claim_3_domain = list(sum_triples(48, cap=24))
claim_3_failures = [t for t in claim_3_domain if sum(x > 0 for x in t) < 2]
claim_4_value = 6 * 1 + 60 * 1 + 6 * 2
claim_5_domain = list(range(79, 218))
claim_5_failures = [
    {"F": f, "natural_difference": nat_sub(1008, f)}
    for f in claim_5_domain
    if not 791 <= nat_sub(1008, f) <= 929
]

control_1_domain = list(sum_triples(71, cap=24))
control_1_counterexamples = [t for t in control_1_domain if t != (24, 24, 24)]
control_3_domain = list(sum_triples(48))
control_3_counterexamples = [t for t in control_3_domain if sum(x > 0 for x in t) < 2]
control_2_domain = list(sum_triples(0))
control_2_counterexamples = [t for t in control_2_domain if not any(0 < x < 24 for x in t)]

assert claim_1_domain == [(24, 24, 24)]
assert not claim_1_failures
assert len(claim_2_domain) == 91 and not claim_2_failures
assert len(claim_3_domain) == 325 and not claim_3_failures
assert claim_4_value == 78
assert len(claim_5_domain) == 139 and not claim_5_failures
assert control_1_counterexamples == [(23, 24, 24), (24, 23, 24), (24, 24, 23)]
assert control_3_counterexamples == [(0, 0, 48), (0, 48, 0), (48, 0, 0)]
assert control_2_counterexamples == [(0, 0, 0)]
assert nat_sub(1008, 79) == 929
assert nat_sub(1008, 217) == 791
assert nat_sub(1008, 78) == 930
assert nat_sub(1008, 218) == 790

result = {
    "input_path": INPUT,
    "input_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "source_revision_supplied_by_parent": "639fb3de7",
    "source_revision_independently_verified": False,
    "claims": {
        "A1": {"verdict": "holds", "eligible_triples": len(claim_1_domain), "failures": claim_1_failures},
        "A2": {"verdict": "holds", "eligible_triples": len(claim_2_domain), "failures": claim_2_failures},
        "A3": {"verdict": "holds", "eligible_triples": len(claim_3_domain), "failures": claim_3_failures,
               "exactly_two_positive": [t for t in claim_3_domain if sum(x > 0 for x in t) == 2]},
        "A4": {"verdict": "holds", "evaluated_lhs": claim_4_value, "rhs": 78},
        "A5": {"verdict": "holds", "eligible_F_values": len(claim_5_domain), "failures": claim_5_failures,
               "endpoint_witnesses": [{"F": 79, "natural_difference": 929}, {"F": 217, "natural_difference": 791}]},
    },
    "negative_controls": {
        "A1_at_sum_71": {"verdict": "breaks", "eligible_triples": len(control_1_domain), "all_counterexamples": control_1_counterexamples},
        "A3_without_cap": {"verdict": "breaks", "eligible_triples": len(control_3_domain), "all_counterexamples": control_3_counterexamples},
        "A2_at_sum_zero": {"verdict": "breaks", "eligible_triples": len(control_2_domain), "all_counterexamples": control_2_counterexamples},
    },
    "additional_bound_checks": [
        {"F": 78, "natural_difference": 930, "violated_bound": "<= 929"},
        {"F": 218, "natural_difference": 790, "violated_bound": ">= 791"},
    ],
    "all_assertions_passed": True,
}

with open(OUTPUT, "w", encoding="utf-8") as output_file:
    json.dump(result, output_file, indent=2)
    output_file.write("\n")

print(json.dumps(result, indent=2))
