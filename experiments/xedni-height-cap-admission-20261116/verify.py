"""Independent string-integer replay of frozen height-cap admissions."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
result=json.loads((HERE/"result.json").read_text())
source=ROOT/"xedni-lift-height-search-20261116"/"rows.jsonl"
lifts=ROOT/"xedni-common-preimage-lift-20261116"/"lifts.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol["source_candidate_rows_sha256"]
assert hashlib.sha256(lifts.read_bytes()).hexdigest()==protocol["source_lifts_sha256"]
events_path=HERE/"events.jsonl"
assert hashlib.sha256(events_path.read_bytes()).hexdigest()==result["events_sha256"]
rows=[json.loads(line) for line in source.open()]
source_events=[json.loads(line) for line in lifts.open()]
events=[json.loads(line) for line in events_path.open()]
assert len(rows)==4293 and len(source_events)==len(events)==159
caps=protocol["caps_bits"]
totals={str(c):Counter() for c in caps}


def part_size(value):
    n,sep,d=str(value).partition("/")
    n=int(n)
    d=int(d) if sep else 1
    assert d>0 and math.gcd(abs(n),d)==1
    return max(abs(n).bit_length(),d.bit_length())


for i,(source_event,event) in enumerate(zip(source_events,events)):
    group=rows[27*i:27*(i+1)]
    assert len(group)==27 and all(row["event_index"]==i for row in group)
    positive=source_event["public_relation"]
    assert event["kind"]==("positive" if positive else "negative_control")
    sizes=[]
    for row in group:
        assert row["P_reduction"]==source_event["U"]
        assert (row["R_reduction"]==source_event["V"])==positive
        size=max(part_size(v) for v in (row["A"],row["B"],*row["P"],*row["R"]))
        sizes.append(size)
    assert event["baseline_height_bits"]==sizes[13]
    assert event["minimum_height_bits"]==min(sizes)
    previous=0
    for cap in caps:
        n=sum(size<=cap for size in sizes)
        assert n>=previous
        previous=n
        baseline=sizes[13]<=cap
        admitted=bool(positive and n>0)
        mismatch=bool(not positive and n>0)
        assert event["caps"][str(cap)]=={
            "bounded_candidates":n,"baseline_bounded":baseline,
            "admitted":admitted,"bounded_control_mismatch":mismatch}
        t=totals[str(cap)]
        if positive:
            t["positive_bounded_candidate_attempts"]+=n
            t["positive_admitted_baseline"]+=int(baseline)
            t["positive_admitted_any"]+=int(admitted)
            t["positive_added_by_shift"]+=int(admitted and not baseline)
        else:
            t["control_bounded_candidate_attempts"]+=n
            t["control_bounded_mismatch_events"]+=int(mismatch)

for cap in caps:
    expected=dict(totals[str(cap)])
    expected["control_admitted"]=0
    assert result["by_cap_bits"][str(cap)]==expected

receipt={"schema":"xedni-height-cap-admission-verification-v1","status":"PASS",
         "method":"independent canonical integer-string bit accounting",
         "source_rows_sha256":protocol["source_candidate_rows_sha256"],
         "events_sha256":result["events_sha256"],
         "caps_checked":caps,"candidate_attempts_checked":len(rows),"events_checked":len(events)}
(HERE/"verification.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
