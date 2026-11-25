"""Classify rational B-branch lifts of the small-prime C-E pairs."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(path):
    spec=importlib.util.spec_from_file_location('j1728_inverse_filter',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    source=HERE/'bad_prime_audit.json';audit=json.loads(source.read_text())
    inverse_path=ROOT/'experiments/hecke-432-inverse-filter-crossprime-20261025/inverse_filter.py'
    resolvent_path=ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    branch_path=ROOT/'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json'
    inverse=load(inverse_path)
    resolvent=json.loads(resolvent_path.read_text())
    branch=json.loads(branch_path.read_text())
    cells=[]
    for cell in audit['cells']:
        p=cell['prime'];squares=defaultdict(list)
        for y in range(p):squares[y*y%p].append(y)
        rows=[]
        for source_row in cell['rows']:
            c=tuple(source_row['C_point'])
            for xe in source_row['rational_x_E_roots']:
                for ye in squares[(xe**3+432)%p]:
                    value=inverse.evaluate_pair(c,(xe,ye),p,resolvent,branch)
                    rows.append({'C_point':list(c),'E_point':[xe,ye],**value})
        assert len(rows)==cell['rational_CE_pairs']
        status=dict(Counter(r['status'] for r in rows))
        cells.append({'prime':p,'rational_CE_pairs':len(rows),'status_mix':status,'rows':rows})
        print(json.dumps({'prime':p,'status_mix':status}),flush=True)
    out={'status':'EXACT_SMALL_PRIME_BRANCH_CLASSIFICATION',
         'bad_prime_audit_sha256':sha256(source.read_bytes()).hexdigest(),
         'inputs':{str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest()
                   for path in (inverse_path,resolvent_path,branch_path)},
         'cells':cells}
    (HERE/'branch_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'valid_triples':sum(c['status_mix'].get('VALID',0) for c in cells)}))


if __name__=='__main__':main()
