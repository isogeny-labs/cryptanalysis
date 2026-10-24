"""Target-directed modular-polynomial screen at six additional prime degrees."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    protocol_path=HERE/'l37_61_protocol.json';raw=protocol_path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_EXTENDED_SCREEN'
    assert protocol['degrees']==[37,41,43,53,59,61]
    prior_path=HERE/'result.json'
    source_path=ROOT/'hecke-higher-degree-screen-20261024/result.json'
    prior=json.loads(prior_path.read_text());source=json.loads(source_path.read_text())
    targets=sorted(int(j) for j in prior['target_js'])
    sources={r['j']:r for r in source['records']}
    assert len(targets)==40 and len(sources)==11619
    F=GF(20023);R=PolynomialRing(F,'Y');Y=R.gen()
    outcomes={}
    for ell in protocol['degrees']:
        print(json.dumps({'degree':ell,'stage':'building_modular_polynomial'}),flush=True)
        phi=classical_modular_polynomial(ell)
        adjacent=defaultdict(set);reverse_counts={}
        for tj in targets:
            roots=R(phi(F(tj),Y)).roots()
            reverse_counts[tj]=sum(int(m) for _,m in roots)
            for sj,_ in roots:
                if int(sj) in sources:adjacent[int(sj)].add(tj)
        rows=[]
        for sj,linked in sorted(adjacent.items()):
            roots=R(phi(F(sj),Y)).roots()
            assert linked<={int(x) for x,_ in roots}
            mult=sum(int(m) for _,m in roots)
            rows.append({'source_j':sj,'source_count':sources[sj]['source_count'],
                         'linked_target_js':sorted(linked),
                         'rational_root_multiplicity':mult,
                         'distinct_rational_roots':len(roots),'fully_split':mult==ell+1})
        outcomes[str(ell)]={'candidate_source_j_count':len(rows),
                            'candidate_source_point_count':sum(r['source_count'] for r in rows),
                            'fully_split_adjacencies':[r for r in rows if r['fully_split']],
                            'candidate_rows':rows,'reverse_root_counts':reverse_counts}
        print(json.dumps({'degree':ell,'candidate_j':len(rows),
                          'fully_split_j':len(outcomes[str(ell)]['fully_split_adjacencies'])}),flush=True)
        del phi
    out={'status':'EXTENDED_TARGETED_MODPOLY_SCREEN_PRODUCED','protocol_sha256':sha(protocol_path),
         'source_sha256':{'prior':sha(prior_path),'source':sha(source_path)},
         'target_j_count':40,'outcomes':outcomes,'candidate_id':None,'timing_claim':None}
    (HERE/'l37_61_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
