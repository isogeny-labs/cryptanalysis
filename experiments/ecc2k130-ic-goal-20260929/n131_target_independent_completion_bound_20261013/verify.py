"""Read-only independent integer audit of the completion bound."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
SOURCE=GOAL/"n41_common_frob_factor_20261012/source_projection_result.json"
TARGET=GOAL/"n41_common_frob_factor_20261012/n131_projection_result.json"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    protocol=read(HERE/"protocol.json")
    result=read(HERE/"count_result.json")
    source=read(SOURCE);target=read(TARGET)
    assert protocol["sha256"]=={"script":sha(HERE/"count.py"),
                                "source":sha(SOURCE),"target":sha(TARGET)}
    assert result["protocol_sha256"]==sha(HERE/"protocol.json")
    assert result["status"]=="PASS_EXACT_N131_TARGET_INDEPENDENT_COMPLETION_BOUND"
    S=int(source["signed_pair_states"])
    r=int(target["subgroup_order"])
    assert S==result["signed_pair_states"]
    assert r==int(result["subgroup_order"])
    assert target["factor_mod_r"]*target["inverse_mod_r"]%r==1
    assert source["curve_id"]==target["curve_id"]==protocol["curve_id"]
    assert source["public_point"]==target["public_point"]
    assert source["transformed_target"]==target["transformed_target"]
    M=(S*S-S)//2
    assert M==int(result["unordered_two_pair_ceiling"])
    assert M==int(result["one_proposal_probability_numerator"])
    assert r==int(result["one_proposal_probability_denominator"])
    assert int(result["half_success_min_proposals"])==(r+2*M-1)//(2*M)
    assert int(result["unit_mean_min_proposals"])==(r+M-1)//M
    for count in protocol["proposal_budgets"]:
        row=result["budget_bounds"][str(count)]
        assert int(row["numerator"])==min(r,count*M)
        assert int(row["denominator"])==r
    output=(HERE/"lean_check.txt").read_text()
    assert "ProposalBound.reachable_length" in output
    assert "sorryAx" not in output
    print("PASS_N131_TARGET_INDEPENDENT_COUNT_RECEIPT")

if __name__=="__main__":main()
