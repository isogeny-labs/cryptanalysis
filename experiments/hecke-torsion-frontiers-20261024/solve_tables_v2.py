"""Anchored modular relation solve and finite one-target offset audit."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import GF, EllipticCurve, ZZ, matrix, vector, crt

HERE=Path(__file__).resolve().parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def one(case,p,h,order,anchor,moduli,seed):
    data=json.loads((HERE/(case+'.result.json')).read_text())
    extra=json.loads((HERE/'p20023.seed.result.json').read_text()) if case=='p20023' else None
    rows=([r['coefficients'] for r in extra['accepted_rows']] if extra else [])+data['rows']
    keys=[tuple(x) for x in data['column_representatives']];index={a:i for i,a in enumerate(keys)}
    E=EllipticCurve(GF(p),[0,-1,1,-10,-20]);O=E(0)
    def point(pair):return O if pair==(-1,-1) else E([pair[0],pair[1],1])
    G=h*point(anchor);assert G!=O and order*G==O
    anchor_orbit=min(key(point(anchor)+k*point((5,5))) for k in range(5))
    a=index[anchor_orbit]
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    entries[(len(rows),a)]=1
    solutions=[];support_by_mod={};ranks={}
    for modulus in moduli:
        F=GF(modulus);M=matrix(F,len(rows)+1,len(keys),entries,sparse=False)
        b=vector(F,[0]*len(rows)+[1]);x=M.solve_right(b)
        assert M*x==b
        basis=M.right_kernel().basis();support=set().union(*(set(v.support()) for v in basis))
        support_by_mod[str(modulus)]=sorted(support)
        ranks[str(modulus)]={'rank':int(M.rank()),'nullity':len(basis),'undetermined_orbits':len(support)}
        solutions.append(x)
    undetermined=set().union(*(set(v) for v in support_by_mod.values()))
    scalars={};P=O
    for k in range(order):
        assert key(P) not in scalars
        scalars[key(P)]=k;P+=G
    assert P==O and len(scalars)==order
    logs={};projected_to_orbit={}
    for i,representative in enumerate(keys):
        if i in undetermined:continue
        point_key=key(h*point(representative))
        log=int(solutions[0][i]) if len(moduli)==1 else int(crt([ZZ(int(x[i])) for x in solutions],moduli))
        assert log==scalars[point_key]
        assert point_key not in logs or logs[point_key]==log
        logs[point_key]=log;projected_to_orbit[point_key]=i
    def recover(Q):
        for offset in range(3):
            shifted=key(Q+offset*G)
            if shifted in logs:
                candidate=(logs[shifted]-offset)%order
                assert candidate*G==Q
                return candidate,offset
        return None,None
    offsets={'0':0,'1':0,'2':0,'uncovered':0}
    for k in range(order):
        answer,offset=recover(k*G)
        if answer is None:offsets['uncovered']+=1
        else:assert answer==k;offsets[str(offset)]+=1
    target_scalar=int.from_bytes(sha256(seed.encode()).digest(),'big')%order
    target=target_scalar*G;answer,offset=recover(target)
    assert answer==target_scalar
    receipt={'status':'PASS_ANCHORED_RELATION_SOLVE_AND_TARGET_REPLAY',
             'case':case,'source_sha256':sha(HERE/(case+'.result.json')),
             'row_count':len(rows),'column_count':len(keys),'subgroup_order':order,
             'moduli':moduli,'anchored_ranks':ranks,'undetermined_orbit_count':len(undetermined),
             'determined_orbit_count':len(keys)-len(undetermined),
             'prepared_table_count':len(logs),'offset_histogram':offsets,
             'target_seed':seed,'target_scalar_fixture':target_scalar,
             'target_point':key(target),'target_recovered_scalar':answer,
             'target_offset':offset,'candidate_id':None,'timing_claim':None}
    (HERE/(case+'.solved.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,sort_keys=True))

def main():
    protocol=json.loads((HERE/'solve.protocol.v2.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_ANCHORED_SOLVE'
    for name,digest in protocol['source_sha256'].items():
        assert sha(HERE/name)==digest
    one('p12043',12043,40,299,(10,3005),[13,23],
        'hecke-layer5-prospective-one-target-20261023')
    one('p20023',20023,5,4021,(1,8630),[4021],
        'hecke-p20023-prospective-one-target-v1')

if __name__=='__main__':main()
