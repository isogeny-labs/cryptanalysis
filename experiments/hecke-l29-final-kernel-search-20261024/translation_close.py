"""Close the last orbit-log kernel by verified generator-shift identities."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, ZZ, matrix, vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol_path=HERE/'translation_protocol.json';raw=protocol_path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_GENERATOR_TRANSLATION_CLOSURE'
    paths={'kernel':HERE/'kernel_result.json',
           'rank':ROOT/'hecke-l29-trace-orbits-20261024/all_rank_result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'seed':ROOT/'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
           'sign':ROOT/'hecke-sign-closure-20261024/result.json',
           'l23':ROOT/'hecke-l23-targeted-20261024/result.v2.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    kernel=data['kernel']
    assert kernel['rank']==3958 and kernel['nullity']==1
    assert kernel['old_support_indices']==protocol['old_ambiguous_orbit_indices']
    keys=[tuple(a) for a in kernel['column_representatives']]
    old=[tuple(a) for a in data['frontier']['column_representatives']]
    l23=[tuple(a) for a in data['l23']['all_column_representatives']]
    l29=[tuple(a) for a in data['l29']['all_column_representatives']]
    assert len(keys)==3959 and len(old)==3949
    idx={a:i for i,a in enumerate(keys)}
    E=EllipticCurve(GF(20023),[0,-1,1,-10,-20]);O=E(0);T=E([5,5,1])
    assert 5*T==O
    def point(a):return O if tuple(a)==(-1,-1) else E([*a,1])
    def orbit(P):return min(key(P+k*T) for k in range(5))
    A=point(protocol['generator_point']);G=5*A
    assert 4021*G==O
    anchor=idx[orbit(A)]
    projected={}
    for i,rep in enumerate(keys):
        Q=5*point(rep)
        assert key(Q) not in projected
        projected[key(Q)]=i
    support={int(i):v for i,v in kernel['kernel_support'].items()}
    attempts=[];selected=[]
    for old_i in protocol['old_ambiguous_orbit_indices']:
        source_i=idx[old[old_i]]
        assert source_i in support
        Q=5*point(old[old_i])
        for offset in (1,2):
            shifted=Q+offset*G
            hit=projected.get(key(shifted))
            record={'old_orbit_index':old_i,'source_column':source_i,
                    'source_projected_point':key(Q),'offset':offset,
                    'shifted_point':key(shifted),'hit_column':hit,
                    'hit_kernel_coefficient':None if hit is None else support.get(hit,0)}
            if hit is not None and hit not in support:
                assert 5*point(keys[hit])==shifted
                coeff=Counter({source_i:1,anchor:offset})
                coeff[hit]-=1
                record['status']='SELECTED_KNOWN_COLUMN'
                record['coefficients']={str(i):v for i,v in coeff.items() if v}
                selected.append(record);attempts.append(record);break
            record['status']='MISSING' if hit is None else 'HIT_AMBIGUOUS_COLUMN'
            attempts.append(record)
        else:raise AssertionError(f'no known-column shift for old orbit {old_i}')
    assert len(selected)==4
    print(json.dumps({'selected_offsets':[(r['old_orbit_index'],r['offset'],r['hit_column']) for r in selected]},sort_keys=True),flush=True)

    def remap(row,reps):return {str(idx[reps[int(j)]]):v for j,v in row.items()}
    rows=[remap(r['coefficients'],old) for r in data['seed']['accepted_rows']]
    rows += [remap(r,old) for r in data['frontier']['rows']]
    rows += [remap(r['coefficients'],old) for r in data['sign']['sign_rows']]
    rows += [remap(r['coefficients'],l23) for r in data['l23']['accepted_rows']]
    rows += [remap(r['coefficients'],l29) for r in data['l29']['accepted_rows']]
    rows += [r['coefficients'] for r in data['rank']['trace_rows']]
    assert len(rows)+1==kernel['matrix_rows']
    def build(extra,ring):
        all_rows=rows+[r['coefficients'] for r in extra]
        entries={(i,int(j)):v for i,row in enumerate(all_rows) for j,v in row.items()}
        entries[(len(all_rows),anchor)]=1
        return matrix(ring,len(all_rows)+1,len(keys),entries,sparse=False)
    one=build(selected[:1],GF(4021))
    combined=build(selected,GF(4021))
    assert one.rank()==combined.rank()==len(keys)
    full_int=build(selected,ZZ)
    exact_rank=int(full_int.rank());assert exact_rank==len(keys)
    old_cols={idx[a] for a in old}
    new_cols=sorted(set(range(len(keys)))-old_cols)
    projection=int(full_int.matrix_from_columns(new_cols).rank())
    assert projection==10 and exact_rank-projection==3949
    rhs=vector(GF(4021),[0]*len(rows)+[0]*len(selected)+[1])
    # The anchor equation is last in build(), after the shift rows.
    logs=combined.solve_right(rhs)
    assert combined*logs==rhs
    assert int(logs[anchor])==1
    table={}
    for i,rep in enumerate(keys):
        Q=5*point(rep);scalar=int(logs[i])
        assert scalar*G==Q
        table[key(Q)]=scalar
    offsets={'0':0,'1':0,'2':0,'uncovered':0}
    for scalar in range(4021):
        target=scalar*G
        for offset in range(3):
            hit=table.get(key(target+offset*G))
            if hit is not None:
                assert (hit-offset)%4021==scalar
                offsets[str(offset)]+=1;break
        else:offsets['uncovered']+=1
    assert offsets['uncovered']==0
    out={'status':'ZERO_GENERIC_SEED_SHIFT_CLOSURE_PRODUCED',
         'protocol_sha256':sha(protocol_path),
         'source_sha256':{k:sha(v) for k,v in paths.items()},
         'attempts':attempts,'selected_rows':selected,
         'first_shift_augmented_rank':int(one.rank()),
         'all_shifts_augmented_rank':int(combined.rank()),
         'exact_integer_rank':exact_rank,
         'new_column_projection_rank':projection,
         'induced_old_rank':exact_rank-projection,
         'column_representatives':keys,
         'logs_by_column':[int(v) for v in logs],
         'prepared_table_count':len(table),'offset_histogram':offsets,
         'generic_seed_logs':0,'candidate_id':None,'timing_claim':None}
    (HERE/'translation_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'first_rank':out['first_shift_augmented_rank'],
                      'exact_rank':exact_rank,'induced_old_rank':out['induced_old_rank'],
                      'offset_histogram':offsets},sort_keys=True))

if __name__=='__main__':main()
