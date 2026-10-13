"""Read-only integrity check of the frozen three-pair experiment."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen=json.loads((HERE/"terminal_protocol.json").read_text())
    mapping={"script":"terminal_audit.py","query_protocol":"protocol.json",
             "query_result":"result.json","query_stdout":"stdout.log",
             "query_stderr":"stderr.log","source":"triple.cpp","binary":"triple",
             "fixture_protocol":"fixture_protocol.json","fixture":"fixture.json",
             "control_protocol":"control_protocol.json","control_result":"control_result.json",
             "control_stdout":"control.stdout","control_stderr":"control.stderr",
             "control_audit_protocol":"control_audit_protocol.json",
             "control_audit_result":"control_audit_result.json","projection":"projection.json"}
    files={key:HERE/name for key,name in mapping.items()}
    files["pairs"]=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
    files["support"]=GOAL/"n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
    assert frozen["status"]=="FROZEN_BEFORE_TERMINAL_AUDIT"
    assert frozen["sha256"]=={key:sha(path) for key,path in files.items()}
    q=json.loads((HERE/"result.json").read_text())
    a=json.loads((HERE/"terminal_audit.json").read_text())
    c=json.loads((HERE/"control_result.json").read_text())
    ca=json.loads((HERE/"control_audit_result.json").read_text())
    assert a["protocol_sha256"]==sha(HERE/"terminal_protocol.json")
    assert (a["corrected_stop_reason"],a["mathematical_outcome"])==("WORKER_QUERY_CAP","BOUNDED_UNKNOWN")
    assert (a["public_outer_families_fully_tested"],a["public_inner_candidates_tested"])==(22304,29568392)
    assert (a["point_matches"],a["column_rejects"],a["public_valid_rows"])==(12,12,0)
    assert q["stdout_sha256"]==sha(HERE/"stdout.log")
    assert q["stderr_sha256"]==sha(HERE/"stderr.log")
    assert c["stdout_sha256"]==sha(HERE/"control.stdout")
    assert c["stderr_sha256"]==sha(HERE/"control.stderr")
    assert ca["status"]=="PASS_INDEPENDENT_CONSTRUCTED_THREEPAIR_CONTROL"
    support=files["support"]
    counts=Counter()
    masks=set()
    for line in support.read_text().splitlines():
        mask,column=map(int,line.split())
        assert mask not in masks
        masks.add(mask)
        counts[column]+=1
    M=len(masks)
    S=4*(M*(M-1)//2-sum(m*(m-1)//2 for m in counts.values()))
    p=json.loads((HERE/"projection.json").read_text())
    r=680564733841876926932320129493409985129
    assert (M,len(counts),S)==(131307,131068,34482792912)
    assert p["n131_signed_pair_states"]==S
    assert Fraction(p["n131_uniform_triple_completion_probability_upper_bound"])==Fraction(S**3,r)
    assert int(p["n131_literal_unordered_two_pair_index_entries"])==S*(S-1)//2
    assert "sorry" not in (HERE/"TripleImageBound.lean").read_text()
    assert "sorryAx" not in (HERE/"lean_check.txt").read_text()
    assert "'triple_image_card_le' depends on axioms: [propext, Quot.sound]" in (HERE/"lean_check.txt").read_text()
    print("PASS_THREEPAIR_READ_ONLY_AUDIT",a["mathematical_outcome"])


if __name__=="__main__":
    main()
