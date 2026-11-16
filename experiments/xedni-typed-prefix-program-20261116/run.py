"""Exhaustively check typed prefix semantics and encoding fibers in Z/7."""
import gzip
import hashlib
import itertools
import json
from collections import Counter
from math import factorial
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root/"protocol.json").read_text())
assert protocol["schema"] == "xedni-typed-prefix-program-protocol-v1"
q = 7
lengths = tuple(protocol["prefix_lengths"])
assert lengths == (2,3,4,5,6)

def forms(labels):
    assert len(labels) >= 2
    fs = [(0,1),(1,0)]
    if len(labels) >= 3:
        fs.append((1,1) if labels[0] < labels[1] else (-1,1))
    if len(labels) >= 4:
        fs.append((0,0))
    if len(labels) >= 5:
        fs.append((0,0))
    if len(labels) >= 6:
        fs.append((0,2))
    return tuple(fs)

def value(form,w):
    return (form[0]*w+form[1])%q

def group_points(w,enc,k):
    pts=[1,w]
    if k>=3:
        pts.append((1+w)%q if enc[1]<enc[w] else (1-w)%q)
    if k>=4: pts.append(0)
    if k>=5: pts.append(0)
    if k>=6: pts.append(2)
    return tuple(pts)

causality=0
for complete in itertools.product(range(q),repeat=6):
    full=forms(complete)
    for k in lengths:
        assert forms(complete[:k]) == full[:k]
        causality+=1
actual=Counter()
group_checks=0
for w in range(q):
    for enc in itertools.permutations(range(q)):
        full=group_points(w,enc,6)
        full_labels=tuple(enc[x] for x in full)
        for k in lengths:
            short=group_points(w,enc,k)
            assert short == full[:k]
            assert tuple(enc[x] for x in short) == full_labels[:k]
            actual[(k,w,full_labels[:k])]+=1
            group_checks+=1
positive=[]
checked=0
zero=0
by_length={k:{"positive":0,"zero":0,"weight":0} for k in lengths}
for k in lengths:
    for w in range(q):
        total=0
        for labels in itertools.product(range(q),repeat=k):
            points=tuple(value(f,w) for f in forms(labels))
            matching=all((labels[i]==labels[j]) == (points[i]==points[j])
                         for i in range(k) for j in range(i))
            expected=factorial(q-len(set(points))) if matching else 0
            observed=actual.get((k,w,labels),0)
            assert observed==expected,(k,w,labels,observed,expected)
            checked+=1
            total+=expected
            if expected:
                positive.append({"k":k,"w":w,"labels":list(labels),"encoding_count":expected})
                by_length[k]["positive"]+=1
                by_length[k]["weight"]+=expected
            else:
                zero+=1
                by_length[k]["zero"]+=1
        assert total==factorial(q)
raw=root/"positive-prefix-fibers.jsonl.gz"
with raw.open("wb") as file:
    with gzip.GzipFile(fileobj=file,mode="wb",mtime=0,filename="") as stream:
        for row in positive:
            stream.write((json.dumps(row,sort_keys=True,separators=(",",":"))+"\n").encode())
result={"schema":"xedni-typed-prefix-program-result-v1","status":"PASS",
        "complete_label_tuples_checked":q**6,
        "form_causality_checks":causality,
        "group_prefix_checks":group_checks,
        "fiber_cells_checked":checked,
        "positive_fiber_cells":len(positive),"zero_fiber_cells":zero,
        "mismatches":0,"by_length":by_length,
        "positive_rows_sha256":hashlib.sha256(raw.read_bytes()).hexdigest()}
assert checked==sum(q**(k+1) for k in lengths)
assert len(positive)+zero==checked
(root/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
