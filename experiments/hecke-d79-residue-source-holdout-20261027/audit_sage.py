"""Independent Sage replay of the prospective p78157 source checkpoints."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE/'inputs.json').read_text())
POST_CLASS = json.loads((HERE/'post-class.json').read_text())
POST_SOURCE = json.loads((HERE/'post-source.json').read_text())


def pinned_local(name, expected):
    raw = (HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)


def sparse(raw):
    return {int(k):int(v) for k,v in raw.items() if v}


def signed_zero(points):
    """Sage point enumeration independent of the producer's affine group law."""
    signed = {(i,s):s*P for i,P in enumerate(points) for s in (-1,1)}
    out=[]
    for support in range(1,5):
        for inds in itertools.combinations(range(40),support):
            for rest in itertools.product((-1,1),repeat=support-1):
                signs=(1,)+rest
                total=points[0].curve()(0)
                for i,s in zip(inds,signs):
                    total+=signed[i,s]
                if total==points[0].curve()(0):
                    out.append((inds,signs))
    return out


def rank(rows,F):
    return int(matrix(F,len(rows),40,lambda i,j:rows[i].get(j,0)).rank())


def main():
    cls=pinned_local('class-result.json',POST_CLASS['class_result_sha256'])
    source=pinned_local('source-result.json',POST_SOURCE['source_result_sha256'])
    assert cls['status']=='CLASS_READY' and source['status']=='CAP40_RANK_DEFICIT'
    c=cls['selected']
    p,q=c['p'],c['largest_prime_factor']
    assert p==source['p']==78157 and q==source['q']==1303
    # Selection rule: no earlier eligible case was skipped.
    eligible=[]
    for v in range(273,c['v']+1,2):
        candidate=v*v+316
        if not is_prime(candidate):continue
        curve=EllipticCurve(GF(candidate),[0,-1,1,-10,-20])
        n=int(curve.cardinality())
        largest=int(max(prime for prime,_ in factor(n)))
        if n%5==0 and (candidate-1)%5!=0 and largest>=53:
            eligible.append(candidate)
    assert eligible==[x['p'] for x in cls['checked_eligible_cases']]==[p]
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    assert int(E.cardinality())==c['curve_order']==78180
    points=[E(x,y) for x,y in c['class_points']]
    assert len(points)==40
    for item in c['base_rows']:
        assert sum((v*points[i] for i,v in sparse(item['row']).items()),E(0))==E(0)
    projection=[(c['curve_order']//5)*P for P in points]
    T=next(P for P in projection if P!=E(0))
    lookup={k*T:k for k in range(5)}
    assert [lookup[P] for P in projection]==c['projection_residues']
    assert source['frozen_source_order']==c['source_order']
    assert sorted(c['source_order'])==list(range(40))
    F=GF(q)
    direct_signed=signed_zero(points)
    direct=[{i:s for i,s in zip(inds,signs)} for inds,signs in direct_signed]
    baseline=[sparse(x['row']) for x in c['base_rows']]+direct
    base_rank=rank(baseline,F)
    assert len(direct)==source['direct_candidate_count']==209
    assert base_rank==source['baseline_rank_mod_q']==32
    entries={x['source']:x for x in source['source_entries']}
    assert len(entries)==40 and [x['source'] for x in source['source_entries']]==c['source_order']
    assert all(x['status']=='OUTSIDE_CLASS_TRACE' for x in entries.values())
    totals=[]
    for i in range(40):
        entry=entries[i]
        total=sum((E(x,y) for x,y in entry['outside_traces']),E(0))
        class_total=sum((v*points[j] for j,v in sparse(entry['class_part']).items()),E(0))
        assert total+class_total==E(0)
        totals.append(total)
    signed_hecke=signed_zero(totals)
    assert all(len(inds)==4 for inds,_ in signed_hecke)
    residue1_hist=Counter(sum(c['projection_residues'][i]==1 for i in inds)
                          for inds,_ in signed_hecke)
    hecke=[]
    for inds,signs in signed_hecke:
        row=Counter()
        for i,s in zip(inds,signs):
            for j,v in sparse(entries[i]['class_part']).items():
                row[j]+=s*v
        row={j:v for j,v in row.items() if v}
        assert sum((v*points[j] for j,v in row.items()),E(0))==E(0)
        hecke.append((set(inds),row))
    assert len(hecke)==source['checkpoints'][-1]['candidate_count']==194
    assert dict(residue1_hist)=={0:1,2:193}
    def path(order):
        rows=[]
        for count in PLAN['checkpoints']:
            seen=set(order[:count])
            chosen=[row for support,row in hecke if support<=seen]
            rows.append({'source_count':count,'candidate_count':len(chosen),
                         'rank_mod_q':rank(baseline+chosen,F)})
        return rows
    new_path=path(c['source_order'])
    old_path=path(c['old_priority_order'])
    assert new_path==[{k:x[k] for k in ('source_count','candidate_count','rank_mod_q')}
                      for x in source['checkpoints']]
    assert new_path[-1]['rank_mod_q']==old_path[-1]['rank_mod_q']==33
    out={'schema':'hecke-d79-residue-source-audit-v1','status':'PASS',
         'p':p,'q':q,'class_points':40,'direct_candidates':len(direct),
         'hecke_candidates':len(hecke),'baseline_rank_mod_q':base_rank,
         'new_order_checkpoints':new_path,'old_priority_checkpoints':old_path,
         'hecke_residue1_source_histogram':{str(k):v for k,v in sorted(residue1_hist.items())},
         'hecke_candidate_supports':[list(inds) for inds,_ in signed_hecke],
         'source_group_equations_verified':len(entries),
         'hecke_group_rows_verified':len(hecke)}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','p':p,'baseline_rank':base_rank,
                      'final_rank':new_path[-1]['rank_mod_q'],
                      'new_path':new_path,'old_path':old_path}))


if __name__=='__main__':
    main()
