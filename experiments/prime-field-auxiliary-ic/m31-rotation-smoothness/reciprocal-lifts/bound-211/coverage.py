"""Count complete archived siblings in each of the two native censuses."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
p = 2**31 - 1
archive = json.loads((here.parent / "archive-overlap/result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git","show",f"{archive['archive']}:{path}"],cwd=here)
assert hashlib.sha256(raw).hexdigest() == archive["fixture_sha256"]
fixture = json.loads(raw)
result = []
for bound, helper in zip((89,211),sys.argv[1:],strict=True):
    values = map(int,subprocess.check_output([str(Path(helper).resolve())]).splitlines())
    keys = {k for x in values for k in (pow(x,31,p),pow(x,-31,p))}
    xs = fixture["structured_roots"]
    rows = []
    for step in fixture["auxiliary"]["maps"]:
        b = step["B"]
        us = {(x-step["r"]) % p for x in xs}
        pairs = [(u,v) for u in sorted(us) if u < (v := b*pow(u,-1,p) % p)]
        s0 = pow(pow(b,-1,p),(p+1)//4,p)
        assert s0*s0*b % p == 1
        hits = []
        for sign in (1,-1):
            s = sign*s0 % p
            for u,v in pairs:
                if pow(s*u,31,p) in keys and pow(s*v,31,p) in keys:
                    hits.append([s,u,v])
        rows.append(dict(sibling_pairs=len(pairs),hits_up_to_rotation=hits))
        xs = [(u+step["A"]+v) % p for u,v in pairs]
    assert xs == [fixture["auxiliary"]["terminal_c"]]
    result.append(dict(bound=bound,orbit_pairs=len(keys)//2,levels=rows))
print(json.dumps(result,indent=2))
