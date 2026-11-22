"""Independent Sage rank replay for every frozen fixed-code z fiber."""
import hashlib
import json
import time
from collections import Counter,defaultdict
from pathlib import Path

from sage.all import GF,matrix

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/"affine_audit_protocol.json").read_text())
for path,digest in p["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"affine_audit_result.json").exists()
started=time.monotonic()
support=json.loads(Path(p["support"]).read_text())
source=json.loads(Path(p["states"]).read_text())
prior=json.loads((HERE/"affine_result.json").read_text())
bits=[i for i in range(9) if i!=5]


def code_of(state):
    mask=state["masks"][0]
    return sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))


codes=[[code_of(state) for state in source["states"][slot]] for slot in (3,4)]
fibers=defaultdict(list)
for w,z,i,j in support:
    fibers[(codes[0][i],codes[1][j])].append(z)

hist=Counter()
for values in fibers.values():
    center=values[0]
    rows=[[(value^center)>>bit&1 for bit in range(41)] for value in values[1:]]
    dimension=matrix(GF(2),rows).rank()
    hist[(len(values),int(dimension))]+=1
expected={f"{size},{dim}":count for (size,dim),count in sorted(hist.items())}
assert expected==prior["size_dimension_histogram"]
assert len(fibers)==prior["usable_code_pairs"]
end=time.monotonic()
out={"status":"PASS_SAGE_ALL_FIXED_CODE_AFFINE_RANKS",
     "candidate_id":None,"curve_id":source["curve_id"],
     "code_pairs_checked":len(fibers),"rows_checked":len(support),
     "size_dimension_histogram":expected,
     "arithmetic_wall_seconds":end-started,
     "protocol_sha256":hashlib.sha256((HERE/"affine_audit_protocol.json").read_bytes()).hexdigest()}
(HERE/"affine_audit_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
