"""Independent low-pivot replay of both exact feature-rank claims."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"verify_retry_protocol.json"
protocol=json.loads(protocol_path.read_text())
for path,digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
assert not (HERE/"verification_retry_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f:(_ for _ in ()).throw(TimeoutError("low-pivot verification wall cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
families=json.loads((HERE/"families.json").read_text())
export=json.loads((HERE/"export_result.json").read_text())
rank=json.loads((HERE/"rank_result.json").read_text())
both=json.loads((HERE/"both_result.json").read_text())
audit=json.loads((HERE/"audit_result.json").read_text())
assert export["status"]=="PASS_N41_TWO_CODE_RECIPROCAL_EXPORT"
assert audit["status"]=="PASS_INDEPENDENT_N41_TWO_CODE_X_AUDIT"
assert audit["assignments"]==16*len(export["rows"])==39712
assert export["completed_families"]==families["eligible_ordered_pairs"]==2482
assert [r["codes"] for r in export["rows"]]==families["selected_pairs"]
assert all(r["distinct_reciprocal_x"]==8 and len(set(r["reciprocal_x"]))==8
           for r in export["rows"])
assert export["positive_reciprocal_x"] in export["rows"][0]["reciprocal_x"]
assert rank["rank"]==5712 and both["rank"]==5754
assert both["first_full"]=={"orientation":"reversed","family":7,"rows":19912}
lean=(HERE/"lean_check.log").read_text()
assert "error:" not in lean and "sorryAx" not in lean
assert "'TwoCodeTraceRank.full_rank_sample_excludes_filter' depends on axioms:" in lean

monomials=[0]+[1<<i for i in range(16)]+[(1<<i)|(1<<j) for i in range(16) for j in range(i+1,16)]
assert len(monomials)==137


def low_insert(pivots,v):
    while v:
        bit=(v&-v).bit_length()-1
        if bit in pivots:
            v^=pivots[bit]
        else:
            pivots[bit]=v
            return


code_pivots={}
for family in export["rows"]:
    left,right=family["codes"]
    assert left<right
    assert not ((left>>7)&1 and not ((right>>7)&1))
    code=left|(right<<8)
    v=sum(1<<i for i,m in enumerate(monomials) if code&m==m)
    low_insert(code_pivots,v)
assert len(code_pivots)==136
original_pivots={}
for family in export["rows"]:
    left,right=family["codes"]
    code=left|(right<<8)
    active=[i for i,m in enumerate(monomials) if code&m==m]
    for z in dict.fromkeys(family["reciprocal_x"]):
        atom=1|(int(z)<<1)
        vector=sum(atom<<(42*i) for i in active)
        low_insert(original_pivots,vector)
assert len(original_pivots)==5712
all_pivots=original_pivots.copy()
first_full=None
for family_number,family in enumerate(export["rows"],1):
    left,right=family["codes"]
    code=right|(left<<8)
    active=[i for i,m in enumerate(monomials) if code&m==m]
    for z in dict.fromkeys(family["reciprocal_x"]):
        atom=1|(int(z)<<1)
        vector=sum(atom<<(42*i) for i in active)
        low_insert(all_pivots,vector)
    if len(all_pivots)==5754:
        first_full=family_number
        break
assert first_full==7
signal.alarm(0)
result={"status":"PASS_INDEPENDENT_N41_TWO_CODE_RANK_AUDIT",
        "candidate_id":None,"curve_id":protocol["curve_id"],
        "code_monomial_rank":len(code_pivots),
        "ordered_feature_rank":len(original_pivots),
        "both_orientation_rank":len(all_pivots),
        "first_full_reversed_family":first_full,
        "wall_seconds":time.monotonic()-started,
        "self_maxrss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "protocol_sha256":hashlib.sha256(protocol_path.read_bytes()).hexdigest()}
(HERE/"verification_retry_result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result),flush=True)
