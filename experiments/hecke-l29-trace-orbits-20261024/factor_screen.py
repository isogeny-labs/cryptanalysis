"""Factor degree-29 Hecke x-fibers at sources touching the new columns."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    path=HERE/'protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_FACTOR_SCREEN'
    screen_path=ROOT/'hecke-l29-closure-20261024/screen_result.json'
    functions_path=ROOT/'hecke-degree-next-screen-20261024/l29_functions.json'
    screen=json.loads(screen_path.read_text());saved=json.loads(functions_path.read_text())
    F=GF(20023);funcs={}
    for tag,coeff in saved['functions'].items():
        ell,part,k=tag.split(':')
        funcs[(int(ell),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[29])
    rows=[];seen=set()
    for candidate in screen['candidate_rows']:
        for point in candidate['source_points']:
            P=tuple(point)
            if P in seen:continue
            seen.add(P)
            Q=rd.E([*P,1]);assert int(rd.j(Q))==candidate['source_j']
            polynomial=rd.neighbour_x(29,Q)
            factors=polynomial.factor()
            profile=[{'degree':int(f.degree()),'multiplicity':int(m),
                      'coefficients':[int(c) for c in f.list()]}
                     for f,m in factors]
            assert sum(r['degree']*r['multiplicity'] for r in profile)==30
            squarefree=all(r['multiplicity']==1 for r in profile)
            rows.append({'source':P,'source_j':candidate['source_j'],
                         'linked_new_target_js':candidate['linked_new_target_js'],
                         'squarefree':squarefree,
                         'rational_x_root_multiplicity':sum(r['multiplicity'] for r in profile if r['degree']==1),
                         'max_factor_degree':max(r['degree'] for r in profile),
                         'factors':profile})
    summary={'source_points':len(rows),'squarefree_source_points':sum(r['squarefree'] for r in rows),
             'degree_profiles':dict(Counter(str(sorted((f['degree'],f['multiplicity']) for f in r['factors'])) for r in rows)),
             'max_factor_degree_histogram':dict(Counter(str(r['max_factor_degree']) for r in rows))}
    out={'status':'L29_PARTIAL_FIBER_FACTORS_PRODUCED','protocol_sha256':sha(path),
         'source_sha256':{'closure_screen':sha(screen_path),'functions':sha(functions_path)},
         'rows':rows,'summary':summary,'candidate_id':None,'timing_claim':None}
    (HERE/'factor_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':main()
