"""Exact GF(2) affine-rank census of usable fixed-code z fibers."""
import hashlib
import json
import time
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/"affine_protocol.json").read_text())
for path,digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"affine_result.json").exists()
started=time.monotonic()
support=json.loads(Path(p["support"]).read_text())
source=json.loads(Path(p["states"]).read_text())
audit=json.loads(Path(p["support_audit"]).read_text())
assert audit["status"]=="PASS_SAGE_FULL_JOINT_RESIDUAL_REPLAY"
assert len(support)==audit["support_rows_checked"]==79424
bits=[i for i in range(9) if i!=5]


def code_of(state):
    mask=state["masks"][0]
    return sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))


codes=[[code_of(state) for state in source["states"][slot]] for slot in (3,4)]
fibers=defaultdict(list)
for w,z,prior_id,last_id in support:
    assert 0<=z<(1<<41) and 0<=w<(1<<41)
    fibers[(codes[0][prior_id],codes[1][last_id])].append(z)


def rank(vectors):
    pivots={}
    for value in vectors:
        x=value
        while x:
            lead=x.bit_length()-1
            if lead in pivots:
                x^=pivots[lead]
            else:
                pivots[lead]=x
                break
    return len(pivots)


hist=Counter()
deficient=[]
for key,values in sorted(fibers.items()):
    assert len(values)==len(set(values))
    dimension=rank(value^values[0] for value in values[1:])
    hist[(len(values),dimension)]+=1
    if dimension<len(values)-1:
        deficient.append({"codes":list(key),"points":len(values),"affine_dimension":dimension})
assert sum(count*size for (size,_),count in hist.items())==len(support)
end=time.monotonic()
out={"status":"PASS_FIXED_CODE_AFFINE_RANK_CENSUS",
     "candidate_id":None,"curve_id":source["curve_id"],
     "usable_code_pairs":len(fibers),
     "excluded_code_pairs":71**2-len(fibers),
     "usable_rows":len(support),
     "size_dimension_histogram":{f"{size},{dim}":count for (size,dim),count in sorted(hist.items())},
     "affine_dependency_pairs":deficient,
     "wall_seconds":end-started,
     "protocol_sha256":hashlib.sha256((HERE/"affine_protocol.json").read_bytes()).hexdigest()}
(HERE/"affine_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
