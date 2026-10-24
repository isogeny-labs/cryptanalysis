"""Independent replay of degree-37 through degree-61 targeted screens."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'extended_validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_EXTENDED_VALIDATION'
    paths={'validator':HERE/'validate_extended.py','l47':HERE/'l47_result.json',
           'extended':HERE/'l37_61_result.json','prior':HERE/'result.json',
           'source':ROOT/'hecke-higher-degree-screen-20261024/result.json'}
    assert protocol['source_sha256']=={k:sha(v) for k,v in paths.items()}
    l47=json.loads(paths['l47'].read_text())
    extended=json.loads(paths['extended'].read_text())
    prior=json.loads(paths['prior'].read_text())
    source=json.loads(paths['source'].read_text())
    targets=sorted(int(j) for j in prior['target_js'])
    sources={r['j']:r for r in source['records']}
    assert len(targets)==40 and len(sources)==11619
    F=GF(20023);R=PolynomialRing(F,'Z');Z=R.gen()
    summary={}
    for ell in [37,41,43,47,53,59,61]:
        saved=l47 if ell==47 else extended['outcomes'][str(ell)]
        phi=classical_modular_polynomial(ell)
        adjacent=defaultdict(set);counts={}
        for tj in targets:
            roots=R(phi(F(tj),Z)).roots()
            counts[tj]=sum(int(m) for _,m in roots)
            for sj,_ in roots:
                if int(sj) in sources:adjacent[int(sj)].add(tj)
        assert {int(j):v for j,v in saved['reverse_root_counts'].items()}==counts
        assert len(adjacent)==saved['candidate_source_j_count']
        rows=saved['candidate_rows']
        assert len(rows)==len(adjacent)
        for row in rows:
            sj=row['source_j']
            linked=adjacent.pop(sj)
            roots=R(phi(F(sj),Z)).roots()
            assert row['source_count']==sources[sj]['source_count']
            assert row['linked_target_js']==sorted(linked)
            assert linked<={int(x) for x,_ in roots}
            assert row['rational_root_multiplicity']==sum(int(m) for _,m in roots)
            assert row['distinct_rational_roots']==len(roots)
            assert row['fully_split']==(row['rational_root_multiplicity']==ell+1)
        assert not adjacent
        assert saved['fully_split_adjacencies']==[r for r in rows if r['fully_split']]
        summary[str(ell)]={'candidate_source_j_count':len(rows),
                           'fully_split_source_j_count':len(saved['fully_split_adjacencies'])}
        print(json.dumps({'degree':ell,'validated':True}),flush=True)
        del phi
    out={'status':'PASS_EXTENDED_MODPOLY_REPLAY','source_sha256':{k:sha(v) for k,v in paths.items()},
         'summary':summary}
    (HERE/'extended_validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
