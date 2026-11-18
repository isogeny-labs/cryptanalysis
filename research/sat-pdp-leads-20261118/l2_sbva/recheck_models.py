#!/usr/bin/env python3
"""Deviation check (see RESULT.md): rows whose arm-A model check failed are
re-solved with CaDiCaL --elim=0 on the identical shuffled CNF, and the full
model is verified clause by clause. Writes model_recheck.json. This does not
change any metric; it only decides whether the SAT answer is backed by a model."""
import json, subprocess, sys
sys.argv = ['x']
import run_l2 as R
S = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/-home-user/ca33b680-080e-5559-8c69-94b98a775c60/scratchpad'
CAD = f'{S}/solvers/cadical/build/cadical'
rows = [json.loads(l) for l in open('rows.jsonl')]
bad = sorted(set((x['file'], x['k']) for x in rows if x.get('model_ok') is False))
out = []
for f, k in bad:
    nv, cls = R.read_cnf(f'{S}/l2inst/{f}')
    sh = R.shuffle_cnf(nv, cls, f"l2-shuffle-{f}-{k}")
    R.write_cnf(f'{S}/chk.cnf', nv, sh)
    o = subprocess.run([CAD, '--elim=0', f'{S}/chk.cnf'], capture_output=True, text=True).stdout
    m = set()
    for line in o.splitlines():
        if line.startswith('v '):
            m.update(int(x) for x in line.split()[1:] if x != '0')
    out.append({"file": f, "k": k, "sat": 's SATISFIABLE' in o, "model_vars": len(m), "nv": nv,
                "model_satisfies": all(any(l in m for l in c) for c in sh)})
json.dump(out, open('model_recheck.json', 'w'), indent=0)
print(sum(r['model_satisfies'] and r['sat'] for r in out), 'of', len(out), 'verified')
