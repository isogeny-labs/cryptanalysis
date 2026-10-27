"""Independent Sage pair-index audit of four full-source gate challenges."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, is_prime, matrix, vector

HERE=Path(__file__).resolve().parent
POST_GATE=json.loads((HERE/'post-gate.json').read_text())
POST_CHALLENGE=json.loads((HERE/'post-challenge.json').read_text())


def local(name,expected):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected
    return json.loads(raw)


def sparse(raw):return {int(k):int(v) for k,v in raw.items() if v}


def zero_relations(points):
    """Find support≤4 cancellations by Sage pair lookup, unlike producer scans."""
    E=points[0].curve()
    signed={(i,s):s*P for i,P in enumerate(points) for s in (-1,1)}
    singles={}
    for k in range(40):
        for sk in (-1,1):singles.setdefault(signed[k,sk],[]).append((k,sk))
    pairs={}
    for k,l in itertools.combinations(range(40),2):
        for sk,sl in itertools.product((-1,1),repeat=2):
            value=signed[k,sk]+signed[l,sl]
            pairs.setdefault(value,[]).append((k,sk,l,sl))
    rows=[]
    for i in range(40):
        if points[i]==E(0):rows.append(((i,),(1,)))
    for i,j in itertools.combinations(range(40),2):
        for sj in (-1,1):
            left=points[i]+signed[j,sj]
            if left==E(0):rows.append(((i,j),(1,sj)))
            for k,sk in singles.get(-left,()):
                if k>j:rows.append(((i,j,k),(1,sj,sk)))
            for k,sk,l,sl in pairs.get(-left,()):
                if k>j:rows.append(((i,j,k,l),(1,sj,sk,sl)))
    assert len(rows)==len(set(rows))
    return rows


def rank(rows,F):
    return int(matrix(F,len(rows),40,lambda i,j:rows[i].get(j,0)).rank())


def main():
    gate=local('gate-result.json',POST_GATE['gate_result_sha256'])
    challenge=local('challenge-result.json',POST_CHALLENGE['challenge_result_sha256'])
    assert gate['status']=='FOUR_GATES_FROZEN' and challenge['status']=='COMPLETE'
    selected=gate['selected']
    assert len(selected)==len(challenge['cases'])==4
    selected_v=selected[-1]['class']['v']
    eligible=[]
    for v in range(303,selected_v+1,2):
        p=v*v+316
        if not is_prime(p):continue
        E0=EllipticCurve(GF(p),[0,-1,1,-10,-20])
        n=int(E0.cardinality())
        largest=int(max(prime for prime,_ in factor(n)))
        if n%5==0 and (p-1)%5!=0 and largest>=53:eligible.append(p)
    assert eligible==[c['p'] for c in gate['checked_eligible_cases']]
    assert eligible==[c['p'] for c in selected]
    cases=[]
    for frozen,produced in zip(selected,challenge['cases']):
        p,q=frozen['p'],frozen['q']
        assert produced['p']==p and produced['q']==q
        c=frozen['class']
        E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
        assert int(E.cardinality())==c['curve_order']
        points=[E(x,y) for x,y in c['class_points']]
        assert len(points)==40
        for item in c['base_rows']:
            assert sum((v*points[i] for i,v in sparse(item['row']).items()),E(0))==E(0)
        projected5=[(c['curve_order']//5)*P for P in points]
        T5=next(P for P in projected5 if P!=E(0))
        lookup5={k*T5:k for k in range(5)}
        assert [lookup5[P] for P in projected5]==c['projection_residues']
        direct_rel=zero_relations(points)
        assert set(direct_rel)=={(tuple(x['indices']),tuple(x['coefficients']))
                                 for x in frozen['direct_candidates']}
        direct=[{i:s for i,s in zip(inds,signs)} for inds,signs in direct_rel]
        baseline=[sparse(x['row']) for x in c['base_rows']]+direct
        F=GF(q)
        base_rank=rank(baseline,F)
        assert base_rank==frozen['baseline_rank_mod_q']==produced['baseline_rank_mod_q']
        assert produced['frozen_gate_decision']==frozen['gate_decision']
        entries=produced['source_entries']
        assert len(entries)==40 and [x['source'] for x in entries]==list(range(40))
        assert all(x['status']=='OUTSIDE_CLASS_TRACE' for x in entries)
        totals=[]
        for entry in entries:
            outside=sum((E(x,y) for x,y in entry['outside_traces']),E(0))
            class_part=sum((v*points[j] for j,v in sparse(entry['class_part']).items()),E(0))
            assert outside+class_part==E(0)
            totals.append(outside)
        hecke_rel=zero_relations(totals)
        hecke=[]
        for inds,signs in hecke_rel:
            row=Counter()
            for i,s in zip(inds,signs):
                for j,v in sparse(entries[i]['class_part']).items():row[j]+=s*v
            row={j:v for j,v in row.items() if v}
            assert sum((v*points[j] for j,v in row.items()),E(0))==E(0)
            hecke.append(row)
        assert len(hecke)==produced['hecke_candidate_count']
        full_rank=rank(baseline+hecke,F)
        assert full_rank==produced['full_pool_rank_mod_q']
        reached=full_rank>=39
        expected=('CORRECT_ACCEPT' if frozen['gate_decision']=='LIFT' else 'FALSE_REJECT') if reached else ('FALSE_ACCEPT' if frozen['gate_decision']=='LIFT' else 'CORRECT_REJECT')
        assert produced['gate_validation']==expected
        cell={'p':p,'q':q,'direct_candidate_count':len(direct),
              'hecke_candidate_count':len(hecke),'baseline_rank_mod_q':base_rank,
              'full_pool_rank_mod_q':full_rank,'rank_gain':full_rank-base_rank,
              'gate_decision':frozen['gate_decision'],'gate_validation':expected,
              'source_group_equations_verified':len(entries),
              'hecke_group_rows_verified':len(hecke)}
        if expected=='FALSE_REJECT':
            assert full_rank==39
            cofactor=c['curve_order']//q
            projected=[cofactor*P for P in points]
            anchor=next(i for i,P in enumerate(projected) if P!=E(0))
            T=projected[anchor]
            assert int(T.order())==q
            rows=baseline+hecke
            A=matrix(F,len(rows),40,lambda i,j:rows[i].get(j,0))
            anchor_row=matrix(F,1,40,lambda _,j:int(j==anchor))
            assert int(A.rank())==39 and int(A.stack(anchor_row).rank())==40
            rhs=vector(F,[0]*A.nrows()+[1])
            logs=[int(x) for x in A.stack(anchor_row).solve_right(rhs)]
            assert all(log*T==P for log,P in zip(logs,projected))
            cell.update({'anchor_index':anchor,'anchor_point':[int(T[0]),int(T[1])],
                         'anchored_logs':logs,'anchored_log_replay':'PASS'})
        cases.append(cell)
        print(json.dumps({'p':p,'baseline_rank':base_rank,'full_rank':full_rank,
                          'gate_validation':expected}),flush=True)
    counts={label:sum(c['gate_validation']==label for c in cases)
            for label in ('CORRECT_ACCEPT','CORRECT_REJECT','FALSE_ACCEPT','FALSE_REJECT','UNKNOWN')}
    assert counts==challenge['gate_counts']
    out={'schema':'hecke-d79-direct-rank-gate-series-audit-v1',
         'status':'PASS','cases':cases,'gate_counts':counts}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','gate_counts':counts}))


if __name__=='__main__':main()
