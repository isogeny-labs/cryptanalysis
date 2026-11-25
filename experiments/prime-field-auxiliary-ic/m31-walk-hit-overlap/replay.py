"""Count short return paths to the fixed public M31 hit set."""
from collections import Counter
from hashlib import sha256
from itertools import combinations_with_replacement
from math import factorial,prod
from pathlib import Path
import csv
import json
import subprocess
import sys
import tempfile

here=Path(__file__).resolve().parent
prefix="experiments/prime-field-auxiliary-ic/snapshot"
def read(path):
    return subprocess.check_output(["git","show",f"f98ac1ca2:{prefix}/{path}"],cwd=here)

opt="algebraic/optimized"
folder=f"{opt}/results/field31_s5_base0"
public=json.loads(read(f"{folder}/public.json"))
source=sha256(read(f"{opt}/native_v2.cpp")).hexdigest()
ns=dict(__name__="public_curve",__file__="prepare.py")
exec(compile(read("prepare.py"),"prepare.py","exec"),ns)
v=public["public"]
curve=ns["Curve"](v["p"],a4=v["a"],a6=v["b"])
basis=list(map(tuple,public["factor_base"]))
signed=basis+list(map(curve.neg,basis))
hits={curve.add(a,b) for a,b in combinations_with_replacement(signed,2)}
hits.remove(None)
assert len(hits)==578
# Negation preserves the hit set, so the ordered sum multiset is also the
# ordered difference multiset. Its coefficient counts all admissible starts.
diff=Counter(curve.add(a,b) for a in hits for b in hits)
assert diff[None]==len(hits) and sum(diff.values())==len(hits)**2
with tempfile.TemporaryDirectory() as tmp:
    binary=Path(tmp)/"steps"
    subprocess.run(["c++","-O2","-std=c++17",str(here/"steps.cpp"),"-o",str(binary)],check=True)
    draws=[tuple(map(int,line.split())) for line in subprocess.check_output([binary]).splitlines()]

writer=csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(["seed","lag","hit_to_hit_paths","starting_hit_and_step_words","hit_rate_ratio"])
for seed in range(3):
    receipt=json.loads(read(f"{folder}/v2_batch_seed{seed}.audited.json"))
    assert receipt["source_sha256"]==source
    steps=[curve.add(curve.mul(a,tuple(v["P"])),curve.mul(b,tuple(v["Q"])))
           for s,a,b in draws if s==seed]
    assert len(set(steps))==len(steps)==32
    for lag in range(1,5):
        paths=words=0
        for ids in combinations_with_replacement(range(32),lag):
            shift=None
            for i in ids: shift=curve.add(shift,steps[i])
            ways=factorial(lag)//prod(factorial(n) for n in Counter(ids).values())
            words+=ways
            paths+=ways*diff[shift]
        assert words==32**lag
        if lag==1:
            assert paths==sum(curve.add(h,s) in hits for h in hits for s in steps)
        denom=len(hits)*words
        writer.writerow([seed,lag,paths,denom,paths*v["n"]/(denom*len(hits))])
