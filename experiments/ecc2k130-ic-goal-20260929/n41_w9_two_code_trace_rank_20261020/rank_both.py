"""Restore both code orientations without repeating commutative group sums."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"both_protocol.json"
protocol=json.loads(protocol_path.read_text())
for path,digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"both_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError("both-orientation rank wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
source=json.loads((HERE/"export_result.json").read_text())
mons=[0]+[1<<i for i in range(16)]+[(1<<i)|(1<<j) for i in range(16) for j in range(i+1,16)]
assert len(mons)*42==5754
pivots={}
phase=[]
processed=0
first_full=None
for orientation in ("original","reversed"):
    for family_number,family in enumerate(source["rows"],1):
        codes=family["codes"] if orientation=="original" else family["codes"][::-1]
        code=codes[0]|(codes[1]<<8)
        active=[i for i,m in enumerate(mons) if code&m==m]
        for value in dict.fromkeys(family["reciprocal_x"]):
            atom=1|(int(value)<<1)
            v=sum(atom<<(42*i) for i in active)
            processed+=1
            while v:
                bit=v.bit_length()-1
                if bit in pivots:v^=pivots[bit]
                else:pivots[bit]=v;break
        if len(pivots)==5754:
            first_full={"orientation":orientation,"family":family_number,"rows":processed}
            break
    phase.append({"orientation":orientation,"families":family_number,
                  "rows":processed,"rank":len(pivots)})
    if first_full:break
signal.alarm(0)
result={"status":"PASS_FULL_RANK_BOTH_ORIENTATIONS" if first_full else "RANK_DEFICIENT_BOTH_ORIENTATIONS",
        "candidate_id":None,"curve_id":protocol["curve_id"],
        "feature_columns":5754,"rank":len(pivots),
        "first_full":first_full,"phases":phase,
        "wall_seconds":time.monotonic()-started,
        "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
(HERE/"both_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":result["status"],"rank":result["rank"],
                  "first_full":first_full,"wall_seconds":result["wall_seconds"]}),flush=True)
