"""Exhaustively compare actual and symbolic fibers for all Z/7 label tuples."""
import gzip
import hashlib
import itertools
import json
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-transcript-fiber-equivalence-protocol-v1"
q = 7

def value(form, w):
    return (form[0]*w + form[1]) % q

def forms_from_labels(labels):
    branch = (1,1) if labels[0] < labels[1] else (-1,1)
    return ((0,1),(1,0),branch,(0,0),(0,0),(0,2))

actual = Counter()
for w in range(q):
    for enc in itertools.permutations(range(q)):
        l0,l1 = enc[1],enc[w]
        branch = (1+w)%q if l0 < l1 else (1-w)%q
        labels = (l0,l1,enc[branch],enc[0],enc[0],enc[2])
        actual[(w,labels)] += 1

positive = []
zero_cells = 0
for w in range(q):
    scalar_total = 0
    for labels in itertools.product(range(q), repeat=6):
        values = tuple(value(f,w) for f in forms_from_labels(labels))
        matching = all((labels[i] == labels[j]) == (values[i] == values[j])
                       for i in range(6) for j in range(i))
        expected = factorial(q-len(set(values))) if matching else 0
        observed = actual.get((w,labels),0)
        assert observed == expected, (w,labels,observed,expected)
        scalar_total += observed
        if expected:
            positive.append({"w":w,"labels":list(labels),"encoding_count":expected})
        else:
            zero_cells += 1
    assert scalar_total == factorial(q)
raw = ROOT / "positive-fibers.jsonl.gz"
with raw.open("wb") as file:
    with gzip.GzipFile(fileobj=file,mode="wb",mtime=0,filename="") as stream:
        for row in positive:
            stream.write((json.dumps(row,sort_keys=True,separators=(",",":"))+"\n").encode())
result = {"schema":"xedni-transcript-fiber-equivalence-result-v1","status":"PASS",
          "scalars":q,"encoding_count":factorial(q),
          "total_execution_pairs":q*factorial(q),
          "proposed_label_tuples_per_scalar":q**6,
          "fiber_cells_checked":q**7,
          "positive_fiber_cells":len(positive),"zero_fiber_cells":zero_cells,
          "fiber_count_mismatches":0,
          "positive_rows_sha256":hashlib.sha256(raw.read_bytes()).hexdigest()}
assert len(positive)+zero_cells == q**7
(ROOT / "result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
