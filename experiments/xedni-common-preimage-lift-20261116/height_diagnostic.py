"""Post hoc exact coordinate-size diagnostic for constructed witnesses."""
import hashlib
import json
import statistics
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/"result.json").read_text())
source=HERE/"lifts.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest()==result["lifts_sha256"]
groups=defaultdict(list)


def bits(value):
    q=Fraction(value)
    return max(abs(q.numerator).bit_length(),q.denominator.bit_length())


for line in source.open():
    row=json.loads(line)
    size=max(bits(z) for z in row["P"]+row["R"])
    groups["positive" if row["public_relation"] else "negative_control"].append(size)

def summarize(values):
    return {"count":len(values),"min_bits":min(values),
            "median_bits":statistics.median(values),"max_bits":max(values)}

receipt={"schema":"xedni-common-preimage-height-diagnostic-v1",
         "status":"complete","classification":"post_hoc_diagnostic",
         "lifts_sha256":result["lifts_sha256"],
         "coordinate_size_definition":"maximum numerator or denominator bit length over x and y of both rational points",
         "groups":{kind:summarize(values) for kind,values in sorted(groups.items())}}
(HERE/"height-diagnostic.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
