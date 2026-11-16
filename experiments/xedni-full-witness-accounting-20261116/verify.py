"""Independent integer-string replay of the two full-witness scores."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
result=json.loads((HERE/"result.json").read_text())
source=ROOT/"xedni-lift-height-search-20261116"/"rows.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol["source_candidate_rows_sha256"]
event_path=HERE/"events.jsonl"
assert hashlib.sha256(event_path.read_bytes()).hexdigest()==result["events_sha256"]
source_rows=[json.loads(line) for line in source.open()]
events=[json.loads(line) for line in event_path.open()]
assert len(source_rows)==4293 and len(events)==159


def integer_parts(value):
    text=str(value)
    numerator,sep,denominator=text.partition("/")
    n=int(numerator)
    d=int(denominator) if sep else 1
    assert d>0 and math.gcd(abs(n),d)==1
    return abs(n).bit_length(),d.bit_length()


def score(row):
    values=(row["A"],row["B"],*row["P"],*row["R"])
    parts=[integer_parts(value) for value in values]
    flat=[bit for pair in parts for bit in pair]
    return max(flat),sum(flat)


def median(values):
    ordered=sorted(values)
    n=len(ordered)
    if n%2:
        return ordered[n//2]
    return (ordered[n//2-1]+ordered[n//2])/2


counts=Counter()
metrics=defaultdict(lambda:defaultdict(list))
for i,event in enumerate(events):
    candidates=source_rows[27*i:27*(i+1)]
    assert len(candidates)==27 and all(row["event_index"]==i for row in candidates)
    assert candidates[13]["shift"]==[0,0,0]
    best_max=min(candidates,key=lambda row:(score(row)[0],tuple(row["shift"])))
    best_sum=min(candidates,key=lambda row:(score(row)[1],tuple(row["shift"])))
    point=min(candidates,key=lambda row:(row["score_bits"],tuple(row["shift"])))
    base=candidates[13]
    assert event["baseline"]=={"full_max_bits":score(base)[0],"full_sum_bits":score(base)[1]}
    assert event["point_winner"]=={"shift":point["shift"],"full_max_bits":score(point)[0],"full_sum_bits":score(point)[1]}
    assert event["full_max_winner"]=={"shift":best_max["shift"],"full_max_bits":score(best_max)[0]}
    assert event["full_sum_winner"]=={"shift":best_sum["shift"],"full_sum_bits":score(best_sum)[1]}
    label=event["kind"]
    assert label==("positive" if point["public_relation"] else "negative_control")
    counts["events"]+=1
    counts[f"{label}_events"]+=1
    counts["max_winner_differs_from_point"]+=int(best_max["shift"]!=point["shift"])
    counts["sum_winner_differs_from_point"]+=int(best_sum["shift"]!=point["shift"])
    counts[f"{label}_sum_winner_differs"]+=int(best_sum["shift"]!=point["shift"])
    for name,value in (("baseline_max",score(base)[0]),("baseline_sum",score(base)[1]),
                       ("point_max",score(point)[0]),("point_sum",score(point)[1]),
                       ("optimum_max",score(best_max)[0]),("optimum_sum",score(best_sum)[1]),
                       ("paired_max_reduction",score(base)[0]-score(best_max)[0]),
                       ("paired_sum_reduction",score(base)[1]-score(best_sum)[1])):
        metrics[label][name].append(value)

assert dict(counts)==result["counts"]
for label,group in metrics.items():
    for name,values in group.items():
        assert result["groups"][label][name]=={"min":min(values),"median":median(values),"max":max(values)}
receipt={"schema":"xedni-full-witness-accounting-verification-v1","status":"PASS",
         "source_rows_sha256":protocol["source_candidate_rows_sha256"],
         "events_sha256":result["events_sha256"],"events_checked":len(events),
         "candidates_checked":len(source_rows),
         "method":"independent canonical integer-string bit accounting"}
(HERE/"verification.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
