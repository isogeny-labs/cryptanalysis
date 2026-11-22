"""Independent Sage point and cubic Boolean-rank replay."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
PAIRS=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
ORIGINAL=GOAL/"n41_two_pair_degree3_filter_20261013/query_receipt.json"
R=549756390943

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    protocol=read(HERE/"audit_protocol.json")
    paths={"script":HERE/"audit_sage.py","pairs":PAIRS,
           "witnesses":HERE/"witnesses.tsv","native":HERE/"native_result.json",
           "query":HERE/"query_receipt.json","runtime":HERE/"sage_runtime_info.json",
           "original_failure":ORIGINAL}
    assert protocol["status"]=="FROZEN_BEFORE_N41_DEGREE3_SAGE_AUDIT"
    assert protocol["sha256"]=={name:sha(path) for name,path in paths.items()}
    native=read(HERE/"native_result.json")
    assert native["status"]=="FULL_DEGREE3_RANK" and native["rank"]==10701
    rows=[]
    for line in (HERE/"witnesses.tsv").read_text().splitlines()[1:]:
        rows.append(tuple(map(int,line.split("\t"))))
    assert len(rows)==10701 and len({row[4] for row in rows})==10701
    needed={sid for row in rows for sid in row[1:3]}
    source={}
    with PAIRS.open() as stream:
        assert stream.readline().split()==["ECC2K41_ALLSEED4","4","4"]
        for line in stream:
            words=line.split()
            if words[0]=="S" and int(words[1])==0:
                sid=int(words[2])
                if sid in needed:source[sid]=tuple(map(int,words[3:]))
    assert set(source)==needed
    ring=PolynomialRing(GF(2),"t");t=ring.gen()
    field=GF(2**41,name="t",modulus=t**41+t**3+1)
    curve=EllipticCurve(field,[1,0,0,0,1])
    def dec(n):return field(ring([(n>>i)&1 for i in range(41)]))
    def enc(a):return sum(int(bit)<<i for i,bit in enumerate(a.polynomial().list()))
    basis_trace=[int((field.gen()**i).trace()) for i in range(41)]
    assert basis_trace==[1]+[0]*40
    projected={sid:4*curve(dec(source[sid][6]),dec(source[sid][7])) for sid in needed}
    pair_index={pair:41+k for k,pair in enumerate(itertools.combinations(range(40),2))}
    triple_index={triple:821+k for k,triple in enumerate(itertools.combinations(range(40),3))}
    assert len(pair_index)==780 and len(triple_index)==9880
    def feature(x):
        assert (x&1)==0
        active=[i for i in range(40) if (x>>(i+1))&1]
        value=1
        for i in active:value|=1<<(1+i)
        for pair in itertools.combinations(active,2):value|=1<<pair_index[pair]
        for triple in itertools.combinations(active,3):value|=1<<triple_index[triple]
        return value
    rank_basis={}
    for attempt,a,b,x,pivot in rows:
        assert len(set(source[a][2:4])|set(source[b][2:4]))==4
        summed=projected[a]+projected[b]
        assert summed!=curve(0) and enc(summed[0])==x
        assert int(summed[0].trace())==0
        v=feature(x)
        while v:
            bit=(v&-v).bit_length()-1
            if bit in rank_basis:v^=rank_basis[bit]
            else:
                assert bit==pivot
                rank_basis[bit]=v;break
        else:raise AssertionError("dependent witness row")
    assert len(rank_basis)==10701
    qx,qy=protocol["transformed_target"]
    target=curve(dec(qx),dec(qy));assert R*target==curve(0)
    for k in range(1,129):
        p=k*target
        assert p!=curve(0) and int(p[0].trace())==0 and (enc(p[0])&1)==0
    result={"status":"PASS_SAGE_N41_DEGREE3_RESIDUAL_RANK_AUDIT",
            "curve_id":protocol["curve_id"],"feature_rank":len(rank_basis),
            "feature_count":10701,"trace_hyperplane_degree3_dimension":10701,
            "checked_group_outputs":len(rows),"distinct_source_states":len(needed),
            "subgroup_multiples_checked":128,
            "trace_basis_ones":[i for i,b in enumerate(basis_trace) if b],
            "audit_protocol_sha256":sha(HERE/"audit_protocol.json")}
    with (HERE/"audit_result.json").open("x") as out:
        json.dump(result,out,sort_keys=True,indent=2);out.write("\n")
    print(result["status"],len(rank_basis),len(rows))

if __name__=="__main__":main()
