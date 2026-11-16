"""Independently audit prefix fibers by group-element orbit assignments."""
import gzip
import hashlib
import itertools
import json
from math import factorial
from pathlib import Path

root=Path(__file__).resolve().parent
q=7
lengths=(2,3,4,5,6)
expected={}
for k in lengths:
    for w in range(q):
        branches=(0,) if k==2 else (1,-1)
        for sign in branches:
            full=(1,w,(1+sign*w)%q,0,0,2)
            points=full[:k]
            distinct=tuple(sorted(set(points)))
            weight=factorial(q-len(distinct))
            for assigned in itertools.permutations(range(q),len(distinct)):
                mapping=dict(zip(distinct,assigned))
                labels=tuple(mapping[x] for x in points)
                if k>=3 and (labels[0]<labels[1]) != (sign==1):
                    continue
                key=(k,w,labels)
                assert key not in expected
                expected[key]=weight
raw=root/"positive-prefix-fibers.jsonl.gz"
observed={}
with gzip.open(raw,"rt") as stream:
    for line in stream:
        row=json.loads(line)
        key=(row["k"],row["w"],tuple(row["labels"]))
        assert key not in observed
        observed[key]=row["encoding_count"]
assert observed==expected
result=json.loads((root/"result.json").read_text())
assert result["positive_rows_sha256"]==hashlib.sha256(raw.read_bytes()).hexdigest()
assert result["positive_fiber_cells"]==len(expected)==17437
assert result["fiber_cells_checked"]==sum(q**(k+1) for k in lengths)==960743
assert result["zero_fiber_cells"]==result["fiber_cells_checked"]-len(expected)==943306
for k in lengths:
    cells=[v for key,v in expected.items() if key[0]==k]
    assert sum(cells)==q*factorial(q)==35280
    assert len(cells)==result["by_length"][str(k)]["positive"]
assert result["form_causality_checks"]==q**6*len(lengths)==588245
assert result["group_prefix_checks"]==q*factorial(q)*len(lengths)==176400
audit={"schema":"xedni-typed-prefix-program-audit-v1","status":"PASS",
       "positive_fibers_checked":len(expected),
       "weight_per_length":q*factorial(q),
       "result_sha256":hashlib.sha256((root/"result.json").read_bytes()).hexdigest()}
(root/"audit.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
