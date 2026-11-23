"""Inputs shared by the frozen M31 matched-basis experiments."""
from hashlib import sha256
from pathlib import Path
from functools import lru_cache
import json
import random
import subprocess

here = Path(__file__).resolve().parent

def sample_basis(seed):
    return [x for x, _ in random.Random(seed).sample(auxiliary_pool(),195)]

@lru_cache(maxsize=1)
def auxiliary_pool():
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
    return sorted(pool)

def smooth_basis():
    frozen=(here.parent/"m31-basis-mask/coordinates.txt").read_bytes()
    assert sha256(frozen).hexdigest()=="e7ddb831369de7724ca977022707d844512ccfe0191cb2c5daf5a22ad84a6203"
    return list(map(int,frozen.splitlines()))
