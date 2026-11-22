"""Exact fixed-code proposal coverage ceilings for the frozen seven-pair laws."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W20 = ROOT / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"
N41 = ROOT / "n41_w8_functional_root_table_v2_20261013" / "preflight.json"
SAGE = ROOT / "n41_w8_sign_label_closure_20261013" / "sage_result.json"
SELECTOR = ROOT / "n131_w20_selector_elimination_20261013" / "basis_result.json"
R = {"N131": 680564733841876926932320129493409985129,
     "N41": 549756390943}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ceildiv(a, b):
    return (a + b - 1) // b


def panel(n, r, pair_codes, signed_states):
    assert signed_states == 4 * pair_codes
    rows = []
    for fixed in range(1, 7):
        # Each specified code has exactly four signed point states.
        # All other slots are left unrestricted; ignoring label collisions
        # makes this an upper bound on the number of reachable targets.
        hit_ceiling = 4**fixed * signed_states**(7-fixed)
        proposals_50 = ceildiv(r, 2*hit_ceiling)
        all_code_tuples = pair_codes**fixed
        rows.append({"fixed_code_slots": fixed,
                     "target_count_per_proposal_upper": str(hit_ceiling),
                     "uniform_success_per_proposal_upper_numerator": str(min(r, hit_ceiling)),
                     "uniform_success_denominator": str(r),
                     "proposals_needed_before_half_coverage_permitted": str(proposals_50),
                     "all_ordered_code_tuples": str(all_code_tuples),
                     "minimum_proposal_rate_for_600_seconds": str(ceildiv(proposals_50, 600))})
    return {"field_degree": n, "subgroup_order": str(r),
            "pair_codes_per_slot": pair_codes, "signed_states_per_slot": signed_states,
            "rows": rows}


def result():
    w20 = json.loads(W20.read_text())
    n41 = json.loads(N41.read_text())
    sage = json.loads(SAGE.read_text())
    selector = json.loads(SELECTOR.read_text())
    assert w20["status"] == "PASS_EXACT_W20_SEVEN_PAIR_SOURCE_SUPPORT"
    assert w20["selected_valid_unordered_pairs_per_slot"] == 132045
    assert w20["signed_pair_states_per_slot"] == 528180
    assert n41["exact_pair_codes"] == 40 and n41["root_entries"] == 80
    assert sage["states_checked"] == 1120 and all(s["source_states_checked"] == 160 for s in sage["slots"])
    assert selector["status"] == "PASS_ALL_19_BIT_SOURCE_CODES" and selector["codes_checked"] == 524288
    out = {"status": "PASS_EXACT_FIXED_CODE_CARDINALITY_GATE",
           "candidate_id": None, "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [W20,N41,SAGE,SELECTOR]},
           "coverage_model": "fixed ordered code tuples, optionally selected by bounded target advice; uniform prime-subgroup target",
           "N131": panel(131,R["N131"],132045,528180),
           "N41": panel(41,R["N41"],40,160)}
    return out


if __name__ == "__main__":
    path = HERE / "count_result.json"
    data = result()
    if path.exists():
        assert json.loads(path.read_text()) == data
        print("PASS_EXACT_FIXED_CODE_CARDINALITY_GATE_VERIFY")
    else:
        path.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
        print("PASS_EXACT_FIXED_CODE_CARDINALITY_GATE_WRITE")
