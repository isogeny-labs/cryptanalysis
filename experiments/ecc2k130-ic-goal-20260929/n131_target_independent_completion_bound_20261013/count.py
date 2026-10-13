"""Exact uniform-target counting bound for target-independent proposals."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
SOURCE=GOAL/"n41_common_frob_factor_20261012/source_projection_result.json"
TARGET=GOAL/"n41_common_frob_factor_20261012/n131_projection_result.json"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def ceil(a,b):return (a+b-1)//b

def main():
    protocol=read(HERE/"protocol.json")
    assert protocol["status"]=="FROZEN_BEFORE_N131_COMPLETION_BOUND"
    assert protocol["sha256"]=={"script":sha(HERE/"count.py"),
                                "source":sha(SOURCE),"target":sha(TARGET)}
    source=read(SOURCE);target=read(TARGET)
    assert source["status"]=="PASS_N131_FIVEPAIR_SOURCE_LOWER_BOUND"
    assert target["status"]=="PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    assert source["curve_id"]==target["curve_id"]==protocol["curve_id"]
    assert source["public_point"]==target["public_point"]
    assert source["transformed_target"]==target["transformed_target"]
    S=source["signed_pair_states"]
    r=int(source["fixed_list_2m_by_5m_uniform_hit_denominator"])
    assert r==int(target["subgroup_order"])
    assert S==34482792912 and r==680564733841876926932320129493409985129
    assert (target["factor_mod_r"]*target["inverse_mod_r"])%r==1
    M=S*(S-1)//2
    assert M==594531503488697323416
    budgets=protocol["proposal_budgets"]
    fractions={str(k):{"numerator":str(min(r,k*M)),"denominator":str(r),
                       "decimal_upper_bound":format(float(min(Fraction(k*M,r),1)),".17g")}
               for k in budgets}
    result={"status":"PASS_EXACT_N131_TARGET_INDEPENDENT_COMPLETION_BOUND",
            "candidate_id":None,"curve_id":source["curve_id"],
            "signed_pair_states":S,"subgroup_order":str(r),
            "unordered_two_pair_ceiling":str(M),
            "one_proposal_probability_numerator":str(M),
            "one_proposal_probability_denominator":str(r),
            "half_success_min_proposals":str(ceil(r,2*M)),
            "unit_mean_min_proposals":str(ceil(r,M)),
            "budget_bounds":fractions,
            "protocol_sha256":sha(HERE/"protocol.json")}
    with (HERE/"count_result.json").open("x") as out:
        json.dump(result,out,indent=2,sort_keys=True);out.write("\n")
    print(result["status"],result["half_success_min_proposals"])

if __name__=="__main__":main()
