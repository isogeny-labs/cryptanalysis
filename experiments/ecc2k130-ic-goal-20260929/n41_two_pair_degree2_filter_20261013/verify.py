"""Read-only receipt and GF(2) rank verification for the degree-two gate."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
PAIRS=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def feature(x):
    value=1; k=1
    for i in range(41):
        if (x>>i)&1:value|=1<<k
        k+=1
    for i in range(41):
        for j in range(i+1,41):
            if (x>>i)&1 and (x>>j)&1:value|=1<<k
            k+=1
    assert k==862
    return value

def main():
    protocol=read(HERE/"protocol.json")
    assert protocol["sha256"]=={"source":sha(HERE/"degree2.cpp"),
                                "binary":sha(HERE/"degree2"),"pairs":sha(PAIRS)}
    query=read(HERE/"query_receipt.json")
    native=read(HERE/"native_result.json")
    audit_protocol=read(HERE/"audit_protocol.json")
    audit=read(HERE/"audit_result.json")
    assert query["protocol_sha256"]==sha(HERE/"protocol.json")
    assert query["status"]=="COMPLETE" and query["exit_code"]==0
    assert query["stdout_sha256"]==sha(HERE/"stdout.log")
    assert query["stderr_sha256"]==sha(HERE/"stderr.log")
    assert native["status"]=="RANK_DEFICIT_AT_CAP"
    assert (native["rank"],native["features"],native["attempts"])==(821,862,20000)
    assert native["maxrss_bytes"]<protocol["combined_rss_cap_bytes"]
    assert query["parent_wall_ns"]<protocol["parent_cap_seconds"]*10**9
    paths={"script":HERE/"audit_sage.py","pairs":PAIRS,
           "witnesses":HERE/"witnesses.tsv","native":HERE/"native_result.json",
           "query":HERE/"query_receipt.json","runtime":HERE/"sage_runtime_info.json"}
    assert audit_protocol["sha256"]=={name:sha(path) for name,path in paths.items()}
    assert audit["audit_protocol_sha256"]==sha(HERE/"audit_protocol.json")
    assert audit["status"]=="PASS_SAGE_N41_DEGREE2_RESIDUAL_RANK_AUDIT"
    assert audit["trace_basis_ones"]==[0]
    assert audit["feature_rank"]==audit["trace_hyperplane_degree2_dimension"]==821
    rows=(HERE/"witnesses.tsv").read_text().splitlines()
    assert rows[0]=="attempt\tstate_a\tstate_b\tx\tpivot"
    basis={}; pivots=set(); previous=0
    for line in rows[1:]:
        attempt,a,b,x,pivot=map(int,line.split("\t"))
        assert attempt>previous and a!=b and x>0 and x<1<<41 and (x&1)==0
        assert pivot not in pivots and 0<=pivot<862
        previous=attempt;pivots.add(pivot)
        v=feature(x)
        while v:
            bit=(v&-v).bit_length()-1
            if bit in basis:v^=basis[bit]
            else:basis[bit]=v;break
        else:raise AssertionError("dependent row")
    assert len(basis)==len(rows)-1==821
    assert "does not depend on any axioms" in (HERE/"lean_check.txt").read_text()
    print("PASS_N41_DEGREE2_FILTER_READ_ONLY 821/821")

if __name__=="__main__":main()
