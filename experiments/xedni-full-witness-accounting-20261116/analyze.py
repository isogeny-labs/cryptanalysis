"""Account for curve coefficients and both rational points on frozen lifts."""
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
paths={"candidate":ROOT/"xedni-lift-height-search-20261116"/"rows.jsonl",
       "winners":ROOT/"xedni-lift-height-search-20261116"/"winners.jsonl",
       "sage":ROOT/"xedni-lift-height-search-20261116"/"audit-sage.json"}
for label,path in paths.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==protocol[{
        "candidate":"source_candidate_rows_sha256",
        "winners":"source_point_winners_sha256",
        "sage":"source_sage_audit_sha256"}[label]]
assert json.loads(paths["sage"].read_text())["status"]=="PASS"
candidates=[json.loads(line) for line in paths["candidate"].open()]
point_winners=[json.loads(line) for line in paths["winners"].open()]
assert len(candidates)==159*27 and len(point_winners)==159


def part_bits(value):
    q=Fraction(value)
    return abs(q.numerator).bit_length(),q.denominator.bit_length()


def scores(row):
    parts=[part_bits(z) for z in [row["A"],row["B"],*row["P"],*row["R"]]]
    return max(max(pair) for pair in parts),sum(sum(pair) for pair in parts)


def summary(values):
    return {"min":min(values),"median":statistics.median(values),"max":max(values)}


counts=Counter()
groups=defaultdict(lambda:defaultdict(list))
output=HERE/"events.jsonl"
with output.open("w") as stream:
    for i,point_winner in enumerate(point_winners):
        rows=candidates[i*27:(i+1)*27]
        assert len(rows)==27 and all(r["event_index"]==i and r["status"]=="pass" for r in rows)
        assert rows[13]["shift"]==[0,0,0]
        point_best=min(rows,key=lambda r:(r["score_bits"],*r["shift"]))
        assert point_best["shift"]==point_winner["shift"]
        max_best=min(rows,key=lambda r:(scores(r)[0],*r["shift"]))
        sum_best=min(rows,key=lambda r:(scores(r)[1],*r["shift"]))
        baseline=rows[13]
        label="positive" if point_winner["public_relation"] else "negative_control"
        baseline_max,baseline_sum=scores(baseline)
        point_max,point_sum=scores(point_best)
        optimum_max,_=scores(max_best)
        _,optimum_sum=scores(sum_best)
        record={"event_index":i,"kind":label,"field_prime":point_winner["field_prime"],
                "offsets":point_winner["offsets"],"vector":point_winner["vector"],
                "baseline":{"full_max_bits":baseline_max,"full_sum_bits":baseline_sum},
                "point_winner":{"shift":point_best["shift"],"full_max_bits":point_max,"full_sum_bits":point_sum},
                "full_max_winner":{"shift":max_best["shift"],"full_max_bits":optimum_max},
                "full_sum_winner":{"shift":sum_best["shift"],"full_sum_bits":optimum_sum}}
        stream.write(json.dumps(record,sort_keys=True,separators=(",", ":"))+"\n")
        counts["events"]+=1
        counts[f"{label}_events"]+=1
        counts["max_winner_differs_from_point"]+=int(max_best["shift"]!=point_best["shift"])
        counts["sum_winner_differs_from_point"]+=int(sum_best["shift"]!=point_best["shift"])
        counts[f"{label}_sum_winner_differs"]+=int(sum_best["shift"]!=point_best["shift"])
        for name,value in (("baseline_max",baseline_max),("point_max",point_max),("optimum_max",optimum_max),
                           ("baseline_sum",baseline_sum),("point_sum",point_sum),("optimum_sum",optimum_sum),
                           ("paired_max_reduction",baseline_max-optimum_max),
                           ("paired_sum_reduction",baseline_sum-optimum_sum)):
            groups[label][name].append(value)

assert counts["events"]==159 and counts["positive_events"]==127 and counts["negative_control_events"]==32
assert counts["max_winner_differs_from_point"]==0
result={"schema":"xedni-full-witness-accounting-result-v1","status":"complete",
        "counts":dict(sorted(counts.items())),
        "groups":{label:{name:summary(values) for name,values in sorted(metrics.items())}
                  for label,metrics in sorted(groups.items())},
        "protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
        "events_sha256":hashlib.sha256(output.read_bytes()).hexdigest()}
(HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
