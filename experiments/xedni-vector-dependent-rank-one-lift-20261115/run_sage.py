"""Public-first rank-one rational realization of selected vector relations."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PARENT=ROOT/'xedni-optimized-family-lift-replay-20261115'
OPT=ROOT/'xedni-coefficient-optimization-20261115'
ADAPT=ROOT/'xedni-adaptive-inverse-lift-20261115'
BAND=ROOT/'xedni-crt-band-panel-20261115'
LIFT=ROOT/'xedni-coefficient-family-lift-20261115'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def center(n,p):
    n=int(n)%p
    return n if n<=p//2 else n-p

def reduce_rational(z,p):
    numerator,denominator=int(z.numerator()),int(z.denominator())
    assert denominator%p
    return (numerator*pow(denominator,-1,p))%p

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for key,path in (
        ('parent_public_relation_result_sha256',PARENT/'result.json'),
        ('selected_family_sha256',OPT/'family-selection.json'),
        ('adaptive_inverse_lean_source_sha256',ADAPT/'formal/AdaptiveInverseLift.lean'),
    ):assert protocol[key]==sha(path),key
    vectors=[tuple(v) for v in json.loads((OPT/'family-selection.json').read_text())['selected']]
    assert len(vectors)==13
    parent=load('xedni_rank_one_parent',LIFT/'run.py')
    arith=parent.load_module('xedni_rank_one_arith',parent.ARITH)
    base=[0,0,0,-1,-2]
    reference=json.loads((BAND/'result.json').read_text())
    prior=json.loads((PARENT/'result.json').read_text())['arms'][0]['fields']
    fields=[];total=Counter()
    for old,control in zip(reference['fields'],prior,strict=True):
        p,q=old['field_prime'],old['subgroup_order']
        assert p==control['field_prime'] and q==control['subgroup_order']
        G,Q=tuple(old['generator']),tuple(old['public_target'])
        Ebase=EllipticCurve(GF(p),base)
        Gs,Qs=Ebase(G),Ebase(Q)
        assert int(Gs.order())==q and q*Gs==Ebase(0)
        sampled=[arith.add(Q,arith.neg(arith.mul(t,G,base,p),base,p),base,p) for t in range(q)]
        hits=parent.family_hits(sampled,vectors,q,base,p,arith)
        assert sum(len(v) for v in hits.values())==control['counts']['reduced_family_relations']
        counts=Counter({'queries':q*q,'public_vector_tests':13*(q-1)*(q-2),
                        'public_relations':sum(map(len,hits.values()))})
        rows=[]
        for (t1,t2),matched in hits.items():
            U,V=sampled[t1],sampled[t2]
            for a,b in matched:
                item={'t':[t1,t2],'query_index_one_based':t1*q+t2+1,'vector':[a,b],
                      'status':'started'}
                try:
                    # The group test above precedes construction. Its result is the input here.
                    inverse_b=pow(b%q,-1,q)
                    T=arith.mul(inverse_b,U,base,p)
                    assert T is not None
                    assert parent.signed_mul(b,T,base,arith,p)==U
                    assert parent.signed_mul(-a,T,base,arith,p)==V
                    x,y=center(T[0],p),center(T[1],p)
                    B=y*y-x*x*x+x
                    E=EllipticCurve(QQ,[0,0,0,-1,B])
                    assert E.discriminant()!=0 and (B+2)%p==0
                    P=E([x,y]);A=b*P;C=(-a)*P
                    assert (a*A+b*C).is_zero()
                    assert not A.is_zero() and not C.is_zero()
                    Ar=Ebase([reduce_rational(A[0],p),reduce_rational(A[1],p)])
                    Cr=Ebase([reduce_rational(C[0],p),reduce_rational(C[1],p)])
                    assert Ar==Ebase(U) and Cr==Ebase(V)
                    recovered=((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
                    assert recovered*Gs==Qs
                    coords=[str(A[0]),str(A[1]),str(C[0]),str(C[1])]
                    item.update({'status':'verified','inverse_b':inverse_b,
                                 'lift_T':[x,y],'curve_B':B,
                                 'rational_points_sha256':hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest(),
                                 'recovered_scalar':recovered})
                    counts['verified']+=1
                    counts['modular_inverses']+=1
                    counts['public_scalar_multiplications']+=1
                    counts['curve_constructions']+=1
                    counts['rational_scalar_multiplications']+=2
                    counts['rational_relation_tests']+=1
                    counts['reduction_checks']+=2
                    counts['scalar_replays']+=1
                except Exception as exc:
                    item.update({'status':'failed','error_type':type(exc).__name__,'error':str(exc)})
                    counts['failed']+=1
                rows.append(item)
        path=HERE/f'p{p}-events.jsonl'
        path.write_text(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in rows))
        fields.append({'field_prime':p,'subgroup_order':q,'counts':dict(counts),
                       'events_path':path.name,'events_sha256':sha(path),
                       'first_event':rows[0] if rows else None})
        total.update(counts)
    status='PASS' if total['verified']==protocol['event_cap'] and not total['failed'] else 'INCOMPLETE'
    print(json.dumps({'schema':'xedni-vector-dependent-rank-one-lift-result-v1','status':status,
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),'sage_runtime_sha256':sha(HERE/'sage-runtime-info.json'),
                      'fields':fields,'totals':dict(total)},sort_keys=True,indent=2))

if __name__=='__main__':main()
