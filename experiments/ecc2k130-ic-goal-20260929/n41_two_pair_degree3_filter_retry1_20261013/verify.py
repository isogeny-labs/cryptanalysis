"""Read-only integrity check for the frozen cubic rank and Sage replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
PAIRS=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
ORIGINAL=GOAL/"n41_two_pair_degree3_filter_20261013/query_receipt.json"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    p=read(HERE/"protocol.json")
    assert p["status"]=="FROZEN_BEFORE_N41_DEGREE3_GATE"
    assert p["sha256"]=={"source":sha(HERE/"degree3.cpp"),
                         "binary":sha(HERE/"degree3"),"pairs":sha(PAIRS),
                         "runner":sha(HERE/"run.py")}
    assert p["original_failure_receipt_sha256"]==sha(ORIGINAL)
    q=read(HERE/"query_receipt.json")
    n=read(HERE/"native_result.json")
    a=read(HERE/"audit_result.json")
    ap=read(HERE/"audit_protocol.json")
    assert q["status"]=="COMPLETE" and q["exit_code"]==0
    assert q["protocol_sha256"]==sha(HERE/"protocol.json")
    assert q["stdout_sha256"]==sha(HERE/"stdout.log")
    assert q["stderr_sha256"]==sha(HERE/"stderr.log")
    assert q["parent_wall_ns"]<p["parent_cap_seconds"]*10**9
    assert n["status"]=="FULL_DEGREE3_RANK"
    assert n["features"]==n["rank"]==p["feature_count"]==10701
    assert n["attempts"]<=p["max_attempts"]
    assert n["valid_outputs"]+n["column_rejected"]+n["identity_rejected"]==n["attempts"]
    assert n["maxrss_bytes"]<p["combined_rss_cap_bytes"]
    paths={"script":HERE/"audit_sage.py","pairs":PAIRS,
           "witnesses":HERE/"witnesses.tsv","native":HERE/"native_result.json",
           "query":HERE/"query_receipt.json","runtime":HERE/"sage_runtime_info.json",
           "original_failure":ORIGINAL}
    assert ap["status"]=="FROZEN_BEFORE_N41_DEGREE3_SAGE_AUDIT"
    assert ap["sha256"]=={name:sha(path) for name,path in paths.items()}
    assert a["audit_protocol_sha256"]==sha(HERE/"audit_protocol.json")
    assert a["status"]=="PASS_SAGE_N41_DEGREE3_RESIDUAL_RANK_AUDIT"
    assert a["feature_rank"]==a["trace_hyperplane_degree3_dimension"]==10701
    assert a["trace_basis_ones"]==[0]
    rows=(HERE/"witnesses.tsv").read_text().splitlines()
    assert rows[0]=="attempt\tstate_a\tstate_b\tx\tpivot"
    assert len(rows)-1==10701
    pivots=set();last_attempt=0
    for line in rows[1:]:
        attempt,sa,sb,x,pivot=map(int,line.split("\t"))
        assert attempt>last_attempt and 0<=sa<30952 and 0<=sb<30952
        assert x>0 and x<1<<41 and x%2==0
        assert 0<=pivot<10701 and pivot not in pivots
        pivots.add(pivot);last_attempt=attempt
    assert read(ORIGINAL)["exit_code"]==-11
    print("PASS_N41_DEGREE3_FROZEN_RECEIPTS 10701/10701")

if __name__=="__main__":main()
