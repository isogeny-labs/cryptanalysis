"""Exact rational rank sweep and replay of saved conductor-2 degree-3 cycles."""
import hashlib
import json
from pathlib import Path

from sage.all import QQ, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CASES=(
    (527,'hecke-split3-revised-holdout-20261023'),
    (623,'hecke-split3-qualified-holdout-20261023'),
    (1055,'hecke-floor-overlap-holdout-20261023'),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_kernel(n):
    return 2 if n%3==0 else 0


def cycle_matrix(n):
    out=matrix(QQ,n,n,0)
    for i in range(n):
        out[i,i]+=1
        out[i,(i-1)%n]+=1
        out[i,(i+1)%n]+=1
    return out


def replay_case(d,directory):
    base=ROOT/'experiments'/directory
    data_path=base/'data'/f'exp11_class_walk_D{d}_f6.json'
    audit_path=base/'audit.json'
    cert_path=base/'certificates.json'
    data,audit,certs=(json.loads(path.read_text()) for path in
                      (data_path,audit_path,cert_path))
    assert data['DK']==-d and data['f']==6
    floor={r['column'] for r in audit['point_records'] if r['endomorphism_conductor']==6}
    c2={r['column'] for r in audit['point_records'] if r['endomorphism_conductor']==2}
    row_by_source={r['source_column']:r['row'] for r in audit['row_records']
                   if r['degree']==3 and r['source_conductor']==2}
    assert set(row_by_source)==c2
    cycles=certs['degree3_cycles']
    assert set().union(*(set(c) for c in cycles))==c2
    assert sum(len(c) for c in cycles)==len(c2)
    observations=[]
    for cycle in cycles:
        n=len(cycle)
        assert len(set(cycle))==n
        indexed={col:j for j,col in enumerate(cycle)}
        rows=[]
        for src in cycle:
            raw=data['relation_rows'][row_by_source[src]]
            projected={int(col):int(value) for col,value in raw.items()
                       if int(col) not in floor and value}
            assert set(projected)<=c2
            assert set(projected)<=set(cycle)
            rows.append([projected.get(col,0) for col in cycle])
        actual=matrix(QQ,rows)
        model=cycle_matrix(n)
        assert actual==model,(d,n)
        rank=int(actual.rank())
        assert n-rank==expected_kernel(n),(d,n,rank)
        observations.append({'length':n,'projected_rank_QQ':rank,
                             'kernel_dimension_QQ':n-rank,
                             'matrix_matches_cycle_operator':True})
    return {'d':d,'class_size':data['class_size'],
            'degree3_conductor2_rows':len(c2),'cycles':observations,
            'data_sha256':sha(data_path),'audit_sha256':sha(audit_path),
            'certificates_sha256':sha(cert_path)}


def main():
    sweep=[]
    for n in range(1,97):
        rank=int(cycle_matrix(n).rank())
        assert n-rank==expected_kernel(n),(n,rank)
        sweep.append({'length':n,'rank_QQ':rank,'kernel_dimension_QQ':n-rank})
    cases=[replay_case(d,directory) for d,directory in CASES]
    result={'status':'PASS_GENERAL_CYCLE_MATRIX_AND_SAVED_HECKE_REPLAY',
            'sweep':sweep,'cases':cases,
            'script_sha256':sha(HERE/'sweep.py'),
            'candidate_id':None,'timing_claim':None}
    (HERE/'sweep.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'swept_lengths':len(sweep),
                      'saved_cycles':sum(len(c['cycles']) for c in cases),
                      'saved_cycle_lengths':[[x['length'] for x in c['cycles']] for c in cases]},
                     sort_keys=True))


if __name__=='__main__':main()
