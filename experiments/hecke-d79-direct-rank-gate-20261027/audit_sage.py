"""Independent Sage replay of the p90917 gate and full-source challenge."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix

HERE=Path(__file__).resolve().parent
GATE_POST=json.loads((HERE/'post-gate.json').read_text())
CHALLENGE_POST=json.loads((HERE/'post-challenge.json').read_text())


def local(name,expected):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected
    return json.loads(raw)


def sparse(raw):
    return {int(k):int(v) for k,v in raw.items() if v}


def zero_relations(points):
    E=points[0].curve()
    signed={(i,s):s*P for i,P in enumerate(points) for s in (-1,1)}
    rows=[]
    for support in range(1,5):
        for inds in itertools.combinations(range(40),support):
            for rest in itertools.product((-1,1),repeat=support-1):
                signs=(1,)+rest
                total=E(0)
                for i,s in zip(inds,signs):total+=signed[i,s]
                if total==E(0):rows.append((inds,signs))
    return rows


def rank(rows,F):
    return int(matrix(F,len(rows),40,lambda i,j:rows[i].get(j,0)).rank())


def main():
    gate=local('gate-result.json',GATE_POST['gate_result_sha256'])
    challenge=local('challenge-result.json',CHALLENGE_POST['challenge_result_sha256'])
    assert gate['status']=='GATE_FROZEN' and challenge['status']=='COMPLETE'
    p,q=gate['p'],gate['q']
    assert p==challenge['p']==90917 and q==challenge['q']==89
    eligible=[]
    for v in range(281,gate['selected']['v']+1,2):
        candidate=v*v+316
        if not is_prime(candidate):continue
        E0=EllipticCurve(GF(candidate),[0,-1,1,-10,-20])
        n=int(E0.cardinality())
        largest=int(max(prime for prime,_ in factor(n)))
        if n%5==0 and (candidate-1)%5!=0 and largest>=53:
            eligible.append(candidate)
    assert eligible==[c['p'] for c in gate['checked_eligible_cases']]==[p]
    c=gate['selected']
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
    assert int(E.cardinality())==c['curve_order']==90780
    points=[E(x,y) for x,y in c['class_points']]
    assert len(points)==40
    for item in c['base_rows']:
        assert sum((v*points[i] for i,v in sparse(item['row']).items()),E(0))==E(0)
    projected=[(c['curve_order']//5)*P for P in points]
    T=next(P for P in projected if P!=E(0))
    lookup={i*T:i for i in range(5)}
    assert [lookup[P] for P in projected]==c['projection_residues']
    F=GF(q)
    direct_relations=zero_relations(points)
    direct=[{i:s for i,s in zip(inds,signs)} for inds,signs in direct_relations]
    expected_direct=[sparse(x['row']) for x in gate['direct_candidates']]
    assert direct==expected_direct and len(direct)==gate['direct_candidate_count']==199
    baseline=[sparse(x['row']) for x in c['base_rows']]+direct
    base_rank=rank(baseline,F)
    assert base_rank==gate['baseline_rank_mod_q']==challenge['baseline_rank_mod_q']==32
    assert gate['gate_decision']=='SKIP' and gate['gate_predicts_rank39'] is False
    entries=challenge['source_entries']
    assert len(entries)==40 and [x['source'] for x in entries]==list(range(40))
    assert all(x['status']=='OUTSIDE_CLASS_TRACE' for x in entries)
    totals=[]
    for i,entry in enumerate(entries):
        outside=sum((E(x,y) for x,y in entry['outside_traces']),E(0))
        class_part=sum((v*points[j] for j,v in sparse(entry['class_part']).items()),E(0))
        assert outside+class_part==E(0)
        totals.append(outside)
    hecke_relations=zero_relations(totals)
    hecke=[]
    for inds,signs in hecke_relations:
        row=Counter()
        for i,s in zip(inds,signs):
            for j,v in sparse(entries[i]['class_part']).items():row[j]+=s*v
        row={j:v for j,v in row.items() if v}
        assert sum((v*points[j] for j,v in row.items()),E(0))==E(0)
        hecke.append((set(inds),row))
    assert len(hecke)==challenge['hecke_candidate_count']==201
    full_rank=rank(baseline+[row for _,row in hecke],F)
    assert full_rank==challenge['full_pool_rank_mod_q']==35
    assert challenge['gate_validation']=='CORRECT_REJECT' and challenge['rank39_reached'] is False
    path=[]
    for count in (5,10,15,20,25,30,35,40):
        chosen=[row for support,row in hecke if max(support)<count]
        path.append({'source_count':count,'candidate_count':len(chosen),
                     'rank_mod_q':rank(baseline+chosen,F)})
    support_size_hist=Counter(len(support) for support,_ in hecke)
    residue_hist=Counter(sum(c['projection_residues'][i]==1 for i in support)
                         for support,_ in hecke)
    out={'schema':'hecke-d79-direct-rank-gate-audit-v1','status':'PASS',
         'p':p,'q':q,'baseline_rank_mod_q':base_rank,'full_pool_rank_mod_q':full_rank,
         'direct_candidate_count':len(direct),'hecke_candidate_count':len(hecke),
         'source_group_equations_verified':len(entries),
         'hecke_group_rows_verified':len(hecke),
         'ascending_checkpoints':path,
         'hecke_candidate_supports':[list(inds) for inds,_ in hecke_relations],
         'hecke_support_size_histogram':{str(k):v for k,v in sorted(support_size_hist.items())},
         'hecke_residue1_source_histogram':{str(k):v for k,v in sorted(residue_hist.items())}}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','p':p,'baseline_rank':base_rank,
                      'full_rank':full_rank,'checkpoints':path,
                      'residue_histogram':out['hecke_residue1_source_histogram']}))


if __name__=='__main__':main()
