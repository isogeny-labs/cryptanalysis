"""High-pivot rank of degree-two code-affine reciprocal features."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"rank_protocol.json"
protocol=json.loads(protocol_path.read_text())
for path,digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"rank_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError("rank wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
data=json.loads((HERE/"export_result.json").read_text())
monomials=[0]+[1<<i for i in range(16)]+[(1<<i)|(1<<j) for i in range(16) for j in range(i+1,16)]
assert len(monomials)==137
columns=42*len(monomials)
assert columns==5754
pivots={}
checkpoints=[]
first_full=None
processed_rows=0
for family_number,family in enumerate(data["rows"],1):
    code=family["codes"][0]|(family["codes"][1]<<8)
    active=[i for i,m in enumerate(monomials) if code&m==m]
    for value in dict.fromkeys(family["reciprocal_x"]):
        atom=1|(int(value)<<1)
        v=sum(atom<<(42*i) for i in active)
        processed_rows+=1
        while v:
            bit=v.bit_length()-1
            if bit in pivots:
                v^=pivots[bit]
            else:
                pivots[bit]=v
                break
    if family_number%25==0 or len(pivots)==columns or family_number==len(data["rows"]):
        checkpoints.append({"families":family_number,"rows":processed_rows,"rank":len(pivots)})
    if len(pivots)==columns:
        first_full=family_number
        break
signal.alarm(0)
result={"status":"PASS_FULL_RANK" if first_full else "RANK_DEFICIENT_FULL_CENSUS",
        "candidate_id":None,"curve_id":protocol["curve_id"],
        "degree":2,"code_bits":16,"field_bits":41,"feature_columns":columns,
        "rank":len(pivots),"first_full_family":first_full,
        "processed_families":family_number,"processed_distinct_output_rows":processed_rows,
        "checkpoints":checkpoints,
        "wall_seconds":time.monotonic()-started,
        "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
(HERE/"rank_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":result["status"],"rank":result["rank"],
                  "columns":columns,"processed_families":family_number,
                  "wall_seconds":result["wall_seconds"]}),flush=True)
