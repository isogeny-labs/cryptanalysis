"""Reproduce the three sample bases from the published two-point comparison."""
from pathlib import Path
from hashlib import sha256
import json
import random
import subprocess
import sys

here=Path(__file__).resolve().parent
info=json.loads((here.parent/"m31-batch-smooth/basis-identity.json").read_text())
raw=subprocess.check_output(["git","show",info["roots_commit"]+":"+info["roots_path"]],cwd=here)
assert sha256(raw).hexdigest()==info["roots_file_sha256"]
p=info["field_prime"]
pool=[]
for x in json.loads(raw):
    rhs=(x**3+2*x+14)%p
    y=pow(rhs,(p+1)//4,p)
    if y*y%p==rhs: pool.append((x,min(y,p-y)))
assert len(pool)==16342
frozen=(here.parent/"m31-basis-mask/coordinates.txt").read_bytes()
assert sha256(frozen).hexdigest()=="e7ddb831369de7724ca977022707d844512ccfe0191cb2c5daf5a22ad84a6203"
arms=[list(map(int,frozen.splitlines()))]
for seed in range(3):
    sample=random.Random(seed).sample(sorted(pool),195)
    arms.append([x for x,y in sample])
reverse=sys.argv[2:]==["reverse"]
assert reverse or len(sys.argv)==2
words=[str(x) for arm in arms for x in (reversed(arm) if reverse else arm)]
subprocess.run([sys.argv[1],"matched"],input="\n".join(words),text=True,check=True)
