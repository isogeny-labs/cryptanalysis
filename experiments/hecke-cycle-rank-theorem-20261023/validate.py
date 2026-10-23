"""Independent modular-rank replay of the exact rational cycle sweep."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MODULUS=1000000007


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_mod_dense(rows,q):
    a=[[value%q for value in row] for row in rows]
    pivot=0
    for col in range(len(a[0])):
        chosen=next((i for i in range(pivot,len(a)) if a[i][col]),None)
        if chosen is None:continue
        a[pivot],a[chosen]=a[chosen],a[pivot]
        inv=pow(a[pivot][col],-1,q)
        a[pivot]=[v*inv%q for v in a[pivot]]
        for i in range(pivot+1,len(a)):
            factor=a[i][col]
            if factor:
                a[i]=[(v-factor*w)%q for v,w in zip(a[i],a[pivot])]
        pivot+=1
        if pivot==len(a):break
    return pivot


def model(n):
    a=[[0]*n for _ in range(n)]
    for i in range(n):
        a[i][i]+=1
        a[i][(i-1)%n]+=1
        a[i][(i+1)%n]+=1
    return a


def main():
    sweep=json.loads((HERE/'sweep.json').read_text())
    assert sweep['status']=='PASS_GENERAL_CYCLE_MATRIX_AND_SAVED_HECKE_REPLAY'
    assert sweep['script_sha256']==sha(HERE/'sweep.py')
    assert len(sweep['sweep'])==96
    for index,row in enumerate(sweep['sweep'],1):
        expected=index-(2 if index%3==0 else 0)
        assert row=={'length':index,'rank_QQ':expected,
                     'kernel_dimension_QQ':index-expected}
        assert rank_mod_dense(model(index),MODULUS)==expected
    observed=[]
    for case in sweep['cases']:
        d=case['d']
        directory={527:'hecke-split3-revised-holdout-20261023',
                   623:'hecke-split3-qualified-holdout-20261023',
                   1055:'hecke-floor-overlap-holdout-20261023'}[d]
        base=ROOT/'experiments'/directory
        data_path=base/'data'/f'exp11_class_walk_D{d}_f6.json'
        audit_path=base/'audit.json'
        cert_path=base/'certificates.json'
        assert (case['data_sha256'],case['audit_sha256'],case['certificates_sha256'])==(
            sha(data_path),sha(audit_path),sha(cert_path))
        data,audit,certs=(json.loads(p.read_text()) for p in
                          (data_path,audit_path,cert_path))
        floor={r['column'] for r in audit['point_records'] if r['endomorphism_conductor']==6}
        row_by_source={r['source_column']:r['row'] for r in audit['row_records']
                       if r['degree']==3 and r['source_conductor']==2}
        cycles=certs['degree3_cycles']
        assert len(cycles)==len(case['cycles'])
        for cycle,record in zip(cycles,case['cycles']):
            n=len(cycle)
            assert n==record['length']
            raw_rows=[]
            for src in cycle:
                raw=data['relation_rows'][row_by_source[src]]
                projected={int(k):int(v) for k,v in raw.items() if int(k) not in floor and v}
                assert set(projected)=={src,cycle[(cycle.index(src)-1)%n],
                                        cycle[(cycle.index(src)+1)%n]}
                raw_rows.append([projected.get(col,0) for col in cycle])
            assert raw_rows==model(n)
            rank=rank_mod_dense(raw_rows,MODULUS)
            assert (rank,n-rank)==(record['projected_rank_QQ'],record['kernel_dimension_QQ'])
            observed.append((d,n,rank))
    assert observed==[(527,18,16),(527,18,16),(623,22,22),(623,22,22),
                      (1055,36,34),(1055,36,34)]
    result={'status':'PASS_INDEPENDENT_CYCLE_RANK_REPLAY',
            'sweep_sha256':sha(HERE/'sweep.json'),
            'script_sha256':sha(HERE/'validate.py'),
            'modulus':MODULUS,'exact_sweep_count':96,
            'saved_cycle_count':len(observed),'saved_cycles':observed,
            'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='saved_cycles'},sort_keys=True))


if __name__=='__main__':main()
