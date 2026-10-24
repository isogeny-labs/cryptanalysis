"""Export reciprocal coordinates for all frozen eligible two-code families."""
import hashlib
import json
import resource
import signal
import time
import traceback
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"export_protocol.json"
protocol=json.loads(protocol_path.read_text())
for path,digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"export_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError("N41 output export wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
S=PolynomialRing(GF(2),"u")
u=S.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])


def dec(word):
    return F(S([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


source=json.loads(Path(protocol["states"]).read_text())
families=json.loads(Path(protocol["families"]).read_text())
bits=families["code_bit_order"]


def code(state):
    return sum(((state["masks"][0]>>bit)&1)<<j for j,bit in enumerate(bits))


points=[]
groups=[]
for slot in (0,1):
    row=[]
    grouped={}
    for index,state in enumerate(source["states"][slot]):
        P=E(dec(state["point"][0]),dec(state["point"][1]))
        row.append(P)
        grouped.setdefault(code(state),[]).append(index)
    assert len(grouped)==71 and all(len(v)==4 for v in grouped.values())
    points.append(row)
    groups.append(grouped)
Qraw=E(dec(source["target_raw_point"][0]),dec(source["target_raw_point"][1]))
Q6=E(Qraw[0]**(1<<6),Qraw[1]**(1<<6))
ids=families["positive_state_ids"]
all_states=[E(dec(source["states"][slot][sid]["point"][0]),
              dec(source["states"][slot][sid]["point"][1]))
            for slot,sid in enumerate(ids)]
assert sum(all_states,E(0))==Q6
positive_sum=all_states[0]+all_states[1]
assert positive_sum!=E(0) and positive_sum[0]
positive_z=enc(~positive_sum[0])
rows=[]
status="PASS_N41_TWO_CODE_RECIPROCAL_EXPORT"
error=None
try:
    for left,right in families["selected_pairs"]:
        outputs=[]
        for i in groups[0][left]:
            for j in groups[1][right]:
                P=points[0][i]+points[1][j]
                assert P!=E(0) and P[0]
                outputs.append(enc(~P[0]))
        assert len(outputs)==16
        rows.append({"codes":[left,right],"reciprocal_x":outputs,
                     "distinct_reciprocal_x":len(set(outputs))})
    assert positive_z in rows[0]["reciprocal_x"]
except Exception as exc:
    status="PRODUCER_FAILURE"
    error=traceback.format_exc()
finally:
    signal.alarm(0)
    result={"status":status,"error":error,"candidate_id":None,
            "curve_id":protocol["curve_id"],"rows":rows,
            "positive_reciprocal_x":positive_z,
            "completed_families":len(rows),
            "wall_seconds":time.monotonic()-started,
            "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
    (HERE/"export_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":status,"completed_families":len(rows),
                      "wall_seconds":result["wall_seconds"]}),flush=True)
    if error:
        print(str(exc),flush=True)
