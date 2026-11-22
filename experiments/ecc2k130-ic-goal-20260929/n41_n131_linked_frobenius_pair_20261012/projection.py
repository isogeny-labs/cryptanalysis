"""Conservative labeled-source count for the proposed N131 linked pair."""

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SHIELD = PARENT / "n131_w18_ninepair_orbit_shield_20261012"
sys.path.insert(0, str(SHIELD))
import shield  # noqa: E402

R = 680564733841876926932320129493409985129
N = 33191
SLOTS = 9


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    conflicts = shield.source_conflicts()
    degrees = Counter()
    for a, b in conflicts:
        degrees[a] += 1
        degrees[b] += 1
    assert len(conflicts) == 65 and max(degrees.values()) == 2
    # Each preceding code forbids itself and at most two other codes.
    # This ensures pairwise distinct folded columns across all nine codes.
    lower = math.prod(N - 3 * i for i in range(SLOTS))
    all_labeled = N**SLOTS
    assert lower > R
    # Either root of X^2+X+2 modulo the prime subgroup order is acceptable
    # for proving that the linked factor is nonzero, before choosing the
    # actual Frobenius eigenvalue. Tonelli-Shanks via SymPy supplies roots.
    from sympy.ntheory.residue_ntheory import sqrt_mod
    roots = sorted({((s - 1) * pow(2, -1, R)) % R
                    for s in sqrt_mod(-7, R, all_roots=True)})
    assert len(roots) == 2
    factors = [(1 + pow(root, 16, R)) % R for root in roots]
    assert all(factors)
    result = {
        "status": "PASS_CONSERVATIVE_LABELED_SOURCE_PROJECTION",
        "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "source_codes_per_free_pair": N,
        "free_pair_codes": SLOTS,
        "linked_pair_rotation_gap": 16,
        "forbidden_unequal_code_pairs": len(conflicts),
        "max_unequal_conflict_degree": max(degrees.values()),
        "labeled_code_tuples_unrestricted": str(all_labeled),
        "labeled_code_tuples_admissible_lower_bound": str(lower),
        "subgroup_order": str(R),
        "admissible_tuples_per_group_point_ratio_exact": f"{lower}/{R}",
        "uniform_mapping_heuristic_mean_lower_bound": lower / R,
        "frobenius_eigenvalue_roots_mod_r": list(map(str, roots)),
        "one_plus_lambda_pow_16_for_each_root_mod_r": list(map(str, factors)),
        "interpretation": "Labeled tuple count, not a distinct-target coverage or solver-time bound",
        "sha256": {
            "projection_source": sha(__file__),
            "shield_source": sha(SHIELD / "shield.py"),
            "support_table": sha(shield.orbit9.base.SUPPORT),
        },
    }
    (HERE / "projection_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"], lower, R, factors)


if __name__ == "__main__":
    main()
