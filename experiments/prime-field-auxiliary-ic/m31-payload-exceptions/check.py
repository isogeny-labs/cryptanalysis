"""Offline round-trip and payload counts for signed public archive records."""
import json
import struct
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = "f55d00345:experiments/prime-field-auxiliary-ic/"
def frozen(path):
    return subprocess.check_output(["git", "show", ROOT + path], cwd=HERE)

reader = {"__name__": "public_archive_reference", "__file__": __file__}
exec(compile(frozen("m31-public-pair-build/replay.py"), "reference", "exec"), reader)
p = 2**31 - 1
def check(label, points):
    entries = reader["signed_pair_entries"](points, p)
    compact = reader["encode"]((k//2,v) for k,v in sorted(entries.items()) if k%2==0)
    predicted = dict(reader["decoded_records"](compact))
    if predicted.keys() != entries.keys():
        raise ValueError("Incomplete sign orbit")
    overrides = reader["encode"]((k,v) for k,v in sorted(entries.items()) if predicted[k]!=v)
    for key, value in struct.iter_unpack("<II", overrides):
        if key%2 != 1:
            raise ValueError("Unexpected override on stored orientation")
        predicted[key] = value
    if predicted != entries:
        raise ValueError("Payload mismatch")
    print(label, len(entries), len(compact)//8, len(overrides)//8, sep=",")
    return len(overrides)//8

print("fixture,full_records,base_records,override_records")
for name in ("auxiliary","plain"):
    public = json.loads(frozen(f"snapshot/comparison/field31/{name}/public.json"))
    if check(name, public["factor_base_representatives"]) != 0:
        raise ValueError("Unexpected frozen override count")

# Consecutive public multiples create many repeated finite sums.
x,y = P = (1,814455902)
points = [P]
for i in range(2,65):
    a,b=P
    slope = ((3*x*x+2)*pow(2*y,-1,p) if x==a else (y-b)*pow(x-a,-1,p))%p
    u=(slope*slope-x-a)%p
    x,y=u,(slope*(x-u)-y)%p
    points.append((x,y))
if check("P_3P", [points[0],points[2]]) != 1:
    raise ValueError("Missing collision control")
for k in (8,16,32,64):
    check(f"consecutive_{k}", points[:k])
