"""Independent integer-curve and exact-rank audit of the torsion bridge."""
from collections import Counter,defaultdict
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
P=12043

def sha(path):return sha256(path.read_bytes()).hexdigest()
def on_curve(Q):
    if Q is None:return True
    x,y=Q
    return (y*y+y-x*x*x+x*x+10*x+20)%P==0

def neg(Q):return None if Q is None else (Q[0],(-Q[1]-1)%P)
def add(A,B):
    if A is None:return B
    if B is None:return A
    x1,y1=A;x2,y2=B
    if x1==x2 and (y1+y2+1)%P==0:return None
    if A==B:
        den=(2*y1+1)%P
        assert den
        slope=((3*x1*x1-2*x1-10)*pow(den,-1,P))%P
    else:
        den=(x2-x1)%P
        assert den
        slope=((y2-y1)*pow(den,-1,P))%P
    intercept=(y1-slope*x1)%P
    x3=(slope*slope+1-x1-x2)%P
    y3=(-slope*x3-intercept-1)%P
    Q=(x3,y3)
    assert on_curve(Q)
    return Q

def mul(k,Q):
    if k<0:return mul(-k,neg(Q))
    result=None
    while k:
        if k&1:result=add(result,Q)
        Q=add(Q,Q);k>>=1
    return result

def key(Q):return (-1,-1) if Q is None else Q
def decode(x):return None if tuple(x)==(-1,-1) else tuple(x)

def sparse_rank(rows,modulus=None):
    basis={}
    for row in rows:
        if modulus is None: v={int(j):Fraction(x) for j,x in row.items() if x}
        else:v={int(j):int(x)%modulus for j,x in row.items() if x%modulus}
        while v:
            pivot=min(v)
            if pivot not in basis:
                scale=v[pivot]
                inv=1/scale if modulus is None else pow(scale,-1,modulus)
                basis[pivot]={j:(x*inv if modulus is None else x*inv%modulus)
                              for j,x in v.items() if x}
                break
            factor=v[pivot]
            old=basis[pivot]
            for j,x in old.items():
                new=v.get(j,0)-factor*x
                if modulus is not None:new%=modulus
                if new:v[j]=new
                else:v.pop(j,None)
    return len(basis)

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    private=json.loads((HERE/'private_witness.json').read_text())
    trace=json.loads((HERE/'trace_validation.json').read_text())
    formal=json.loads((HERE/'formal/build.json').read_text())
    data=json.loads(SOURCE.read_text())
    assert protocol['status']=='FROZEN_BEFORE_TORSION_BRIDGE_PRODUCER'
    assert result['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['script_sha256']==protocol['source_sha256']['producer']==sha(HERE/'produce.py')
    assert result['hecke11_sha256']==protocol['source_sha256']['hecke11']==sha(MODULE)
    assert result['source_matrix_sha256']==protocol['source_sha256']['matrix']==sha(SOURCE)
    assert trace['status']=='PASS_TORSION_BRIDGE_TRACE_AND_MODULAR_REPLAY'
    assert trace['result_sha256']==sha(HERE/'result.json')
    assert trace['script_sha256']==sha(HERE/'validate_trace.py')
    assert trace['accepted_cross_class_rows']==40
    assert formal['status']=='LEAN_PRIVATE_PROJECTION_THEOREM_BUILT'
    assert formal['source_sha256']==sha(HERE/'formal/PrivateNewColumns.lean')
    assert formal['output_sha256']==sha(HERE/'formal/build-output.txt')
    assert formal['axioms']==["'PrivateNewColumns.oldOnly_eq_original' depends on axioms: [propext, Quot.sound]"]
    pinned=subprocess.check_output(['git','show',protocol['source_commit']+':'+
                                    str(SOURCE.relative_to(HERE.parent.parent))])
    assert pinned==SOURCE.read_bytes()
    points=[tuple(r['point']) for r in data['column_points']]
    assert len(points)==len(set(points))==120 and all(on_curve(Q) for Q in points)
    T=tuple(protocol['torsion_point']);assert T==(5,5) and on_curve(T)
    assert mul(5,T) is None and all(mul(k,T) is not None for k in range(1,5))
    def orbit(Q):return min(key(add(Q,mul(k,T))) for k in range(5))
    old_keys={orbit(Q) for Q in points}
    sources=defaultdict(list)
    for i,Q in enumerate(points):
        for k in (1,4):sources[add(Q,mul(k,T))].append([i,k])
    new_sources=sorted((Q for Q in sources if Q not in set(points)),key=key)
    assert len(new_sources)==result['translated_new_source_count']==234
    assert len(old_keys)==result['old_orbit_count']==117
    saved={decode(r['point']):r for r in result['source_records']}
    assert set(saved)==set(new_sources)
    assert all(r['origin']==sources[Q] for Q,r in saved.items())
    assert result['torsion_point']==[5,5]
    all_keys=[tuple(x) for x in result['column_representatives']]
    assert all_keys==sorted(set(all_keys))
    old_cols=result['old_column_indices'];new_cols=result['new_column_indices']
    assert set(old_cols).isdisjoint(new_cols) and sorted(old_cols+new_cols)==list(range(len(all_keys)))
    assert {all_keys[i] for i in old_cols}==old_keys
    assert (len(old_cols),len(new_cols))==(117,128)
    ids={key:i for i,key in enumerate(all_keys)}
    base_rows=[]
    for row in data['relation_rows']:
        coeff=Counter()
        group_sum=None
        for col,value in row.items():
            Q=points[int(col)]
            coeff[ids[orbit(Q)]]+=int(value)
            group_sum=add(group_sum,mul(int(value),Q))
        assert group_sum is None
        base_rows.append({str(i):v for i,v in coeff.items() if v})
    assert base_rows==result['base_rows'] and len(base_rows)==70
    accepted=result['accepted_rows'];assert len(accepted)==40
    assert private['status']=='PRIVATE_NEW_COLUMN_WITNESS_FOR_EVERY_CROSS_CLASS_ROW'
    assert private['result_sha256']==sha(HERE/'result.json')
    assert private['script_sha256']==sha(HERE/'certify_private.py')
    assert len(private['witnesses'])==40
    assert len({w['new_column_index'] for w in private['witnesses']})==40
    for i,w in enumerate(private['witnesses']):
        j=w['new_column_index']
        assert w['accepted_row_index']==i and w['full_row_index']==70+i
        assert j in new_cols and w['coefficient']==1
        assert w['orbit_representative']==result['column_representatives'][j]
        assert accepted[i]['coefficients'].get(str(j),0)==1
        assert all(str(j) not in row['coefficients'] for k,row in enumerate(accepted) if k!=i)
        assert all(str(j) not in row for row in base_rows)
    cross=0
    for rec in accepted:
        Q=decode(rec['source']);assert Q in new_sources
        assert rec['origin']==sources[Q]
        l=rec['degree'];assert l in (2,3)
        assert len(rec['neighbours'])==l+1
        neighbours=[decode(x) for x in rec['neighbours']]
        assert all(on_curve(N) for N in neighbours)
        total=None
        for N in neighbours:total=add(total,N)
        assert total==mul(data['hecke_eigenvalues'][str(l)],Q)
        coeff=Counter(ids[orbit(N)] for N in neighbours)
        coeff[ids[orbit(Q)]]-=data['hecke_eigenvalues'][str(l)]
        assert {str(i):v for i,v in coeff.items() if v}==rec['coefficients']
        if rec['source_trace_abs']!=200:cross+=1
    assert cross==result['cross_class_accepted_rows']==40
    all_rows=base_rows+[r['coefficients'] for r in accepted]
    new_only=[{str(j):v for j,v in row.items() if int(j) in set(new_cols)} for row in all_rows]
    exact={'baseline_old_rank':sparse_rank(base_rows),
           'full_rank':sparse_rank(all_rows),
           'new_column_projection_rank':sparse_rank(new_only)}
    exact['induced_old_rank']=exact['full_rank']-exact['new_column_projection_rank']
    exact['induced_increment']=exact['induced_old_rank']-exact['baseline_old_rank']
    assert exact=={'baseline_old_rank':60,'full_rank':100,
                   'new_column_projection_rank':40,'induced_old_rank':60,
                   'induced_increment':0}
    modular={}
    for modulus in (101,1000000007):
        d={'baseline_old_rank':sparse_rank(base_rows,modulus),
           'full_rank':sparse_rank(all_rows,modulus),
           'new_column_projection_rank':sparse_rank(new_only,modulus)}
        d['induced_old_rank']=d['full_rank']-d['new_column_projection_rank']
        d['induced_increment']=d['induced_old_rank']-d['baseline_old_rank']
        modular[str(modulus)]=d
        assert d==exact
        assert all(result['rank_results'][str(modulus)][k]==v for k,v in d.items())
    out={'status':'PASS_TORSION_BRIDGE_ZERO_INDUCED_RANK_CERTIFIED',
         'protocol_sha256':sha(HERE/'protocol.json'),'producer_result_sha256':sha(HERE/'result.json'),
         'private_witness_sha256':sha(HERE/'private_witness.json'),
         'trace_validation_sha256':sha(HERE/'trace_validation.json'),
         'formal_build_sha256':sha(HERE/'formal/build.json'),
         'validator_sha256':sha(HERE/'validate.py'),
         'exact_rational_ranks':exact,'independent_modular_ranks':modular,
         'accepted_cross_class_rows':cross,'old_orbit_columns':len(old_cols),
         'new_orbit_columns':len(new_cols),
         'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exact_rational_ranks':exact},sort_keys=True))

if __name__=='__main__':main()
