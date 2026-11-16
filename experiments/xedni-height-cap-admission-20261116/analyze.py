"""Exact fixed-height admission table on the frozen common-preimage panel."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
source={"rows":ROOT/"xedni-lift-height-search-20261116"/"rows.jsonl",
        "lifts":ROOT/"xedni-common-preimage-lift-20261116"/"lifts.jsonl",
        "sage":ROOT/"xedni-lift-height-search-20261116"/"audit-sage.json"}
for label,path in source.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==protocol[{
        "rows":"source_candidate_rows_sha256","lifts":"source_lifts_sha256",
        "sage":"source_sage_audit_sha256"}[label]]
assert json.loads(source["sage"].read_text())["status"]=="PASS"
candidate_rows=[json.loads(line) for line in source["rows"].open()]
events=[json.loads(line) for line in source["lifts"].open()]
assert len(candidate_rows)==159*27 and len(events)==159
caps=protocol["caps_bits"]
assert caps==sorted(set(caps))


def bits(value):
    z=Fraction(value)
    return max(abs(z.numerator).bit_length(),z.denominator.bit_length())


def height(row):
    return max(bits(z) for z in (row["A"],row["B"],*row["P"],*row["R"]))


counts=Counter()
totals={str(cap):Counter() for cap in caps}
out=HERE/"events.jsonl"
with out.open("w") as stream:
    for i,event in enumerate(events):
        rows=candidate_rows[i*27:(i+1)*27]
        assert len(rows)==27 and all(r["event_index"]==i and r["status"]=="pass" for r in rows)
        assert rows[13]["shift"]==[0,0,0]
        positive=bool(event["public_relation"])
        scores=[]
        for row in rows:
            assert row["public_relation"]==positive
            assert row["P_reduction"]==event["U"]
            assert (row["R_reduction"]==event["V"])==positive
            scores.append(height(row))
        counts["events"]+=1
        counts["positive_events" if positive else "negative_control_events"]+=1
        counts["candidate_attempts"]+=len(rows)
        record={"event_index":i,"field_prime":event["field_prime"],
                "kind":"positive" if positive else "negative_control",
                "vector":event["vector"],"offsets":event["offsets"],
                "baseline_height_bits":scores[13],"minimum_height_bits":min(scores),"caps":{}}
        for cap in caps:
            bounded=sum(score<=cap for score in scores)
            baseline_bounded=scores[13]<=cap
            admitted=positive and bounded>0
            control_mismatch=(not positive) and bounded>0
            record["caps"][str(cap)]={"bounded_candidates":bounded,
                                      "baseline_bounded":baseline_bounded,
                                      "admitted":admitted,
                                      "bounded_control_mismatch":control_mismatch}
            aggregate=totals[str(cap)]
            if positive:
                aggregate["positive_admitted_any"]+=int(admitted)
                aggregate["positive_admitted_baseline"]+=int(baseline_bounded)
                aggregate["positive_added_by_shift"]+=int(admitted and not baseline_bounded)
                aggregate["positive_bounded_candidate_attempts"]+=bounded
            else:
                aggregate["control_bounded_candidate_attempts"]+=bounded
                aggregate["control_bounded_mismatch_events"]+=int(control_mismatch)
                aggregate["control_admitted"]+=int(admitted)
        stream.write(json.dumps(record,sort_keys=True,separators=(",", ":"))+"\n")

assert counts=={"events":159,"positive_events":127,"negative_control_events":32,"candidate_attempts":4293}
for aggregate in totals.values():
    assert aggregate["control_admitted"]==0
result={"schema":"xedni-height-cap-admission-result-v1","status":"complete",
        "counts":dict(sorted(counts.items())),
        "by_cap_bits":{cap:dict(sorted(aggregate.items())) for cap,aggregate in totals.items()},
        "protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
        "events_sha256":hashlib.sha256(out.read_bytes()).hexdigest()}
(HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
