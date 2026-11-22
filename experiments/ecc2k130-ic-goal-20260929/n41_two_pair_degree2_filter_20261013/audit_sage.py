"""Independent Sage point replay and Boolean-rank audit of the N41 witness."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
PAIRS=GOAL/"n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
R=549756390943

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())

def main():
    protocol=read(HERE/"audit_protocol.json")
    paths={"script":HERE/"audit_sage.py","pairs":PAIRS,
           "witnesses":HERE/"witnesses.tsv","native":HERE/"native_result.json",
           "query":HERE/"query_receipt.json","runtime":HERE/"sage_runtime_info.json"}
    assert protocol["status"]=="FROZEN_BEFORE_N41_DEGREE2_SAGE_AUDIT"
    assert protocol["sha256"]=={name:sha(path) for name,path in paths.items()}
    native=read(HERE/"native_result.json")
    assert native["status"]=="RANK_DEFICIT_AT_CAP" and native["rank"]==821
    rows=[]
    for line in (HERE/"witnesses.tsv").read_text().splitlines()[1:]:
        attempt,a,b,x,pivot=map(int,line.split("\t"))
        rows.append((attempt,a,b,x,pivot))
    assert len(rows)==821 and len({row[4] for row in rows})==821
    needed={sid for row in rows for sid in row[1:3]}
    source={}
    with PAIRS.open() as stream:
        assert stream.readline().split()==["ECC2K41_ALLSEED4","4","4"]
        for line in stream:
            words=line.split()
            if words[0]=="S" and int(words[1])==0:
                sid=int(words[2])
                if sid in needed:
                    a,b,ca,cb,sa,sb,x,y=map(int,words[3:])
                    source[sid]=(a,b,ca,cb,sa,sb,x,y)
    assert set(source)==needed
    ring=PolynomialRing(GF(2),"t"); t=ring.gen()
    field=GF(2**41,name="t",modulus=t**41+t**3+1)
    curve=EllipticCurve(field,[1,0,0,0,1])
    def dec(n): return field(ring([(n>>i)&1 for i in range(41)]))
    def enc(a): return sum(int(bit)<<i for i,bit in enumerate(a.polynomial().list()))
    basis_trace=[int((field.gen()**i).trace()) for i in range(41)]
    assert basis_trace==[1]+[0]*40
    projected={sid:4*curve(dec(source[sid][6]),dec(source[sid][7])) for sid in needed}
    features={}
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
    rank_basis={}
    for attempt,a,b,x,pivot in rows:
        ca=set(source[a][2:4]); cb=set(source[b][2:4])
        assert len(ca|cb)==4
        summed=projected[a]+projected[b]
        assert summed!=curve(0) and enc(summed[0])==x
        assert int(summed[0].trace())==0 and (x&1)==0
        v=feature(x)
        while v:
            bit=(v&-v).bit_length()-1
            if bit in rank_basis:v^=rank_basis[bit]
            else:rank_basis[bit]=v;break
        else: raise AssertionError("dependent witness row")
        features[attempt]=x
    assert len(rank_basis)==821
    qx,qy=protocol["transformed_target"]
    target=curve(dec(qx),dec(qy))
    assert R*target==curve(0)
    subgroup_checks=0
    for k in range(1,257):
        point=k*target
        assert point!=curve(0) and int(point[0].trace())==0
        assert enc(point[0])&1==0
        subgroup_checks+=1
    result={"status":"PASS_SAGE_N41_DEGREE2_RESIDUAL_RANK_AUDIT",
            "curve_id":protocol["curve_id"],"feature_rank":len(rank_basis),
            "feature_count":862,"trace_hyperplane_degree2_dimension":821,
            "checked_group_outputs":len(rows),"distinct_source_states":len(needed),
            "subgroup_multiples_checked":subgroup_checks,
            "trace_basis_ones":[i for i,x in enumerate(basis_trace) if x],
            "sample_x_bit0_set_count":sum(x&1 for x in features.values()),
            "audit_protocol_sha256":sha(HERE/"audit_protocol.json")}
    with (HERE/"audit_result.json").open("x") as out:
        json.dump(result,out,sort_keys=True,indent=2);out.write("\n")
    print(result["status"],len(rank_basis),len(rows))

if __name__=="__main__":main()
