#!/usr/bin/env sage -python
"""P-192 depth-2/3 auxiliary fiber with source and horizontal endpoint S5.

Run each process under a wall cap:
 gtimeout 40 /Volumes/SSD990/cryptanalysis/sage -python p192_tower_horizontal_s5.py --mode source --query planted
 gtimeout 40 /Volumes/SSD990/cryptanalysis/sage -python p192_tower_horizontal_s5.py --mode mapped5 --query planted
The same auxiliary fiber defines every arm's source base. This is an
exploratory algebraic component screen, not a relation collector.
"""
import argparse
import hashlib
import itertools
import json
import random
import time
from sage.all import EllipticCurve, GF, PolynomialRing, ZZ, prod

P = 6277101735386680763835789423207666416083908700390324961279
R = 6277101735386680763835789423176059013767194773182842284081
B = int('64210519E59C80E70FA7E9AB72243049FEB8DEECC146B9B1', 16)
GX = int('188DA80EB03090F67CBF20EB43A18800F4FF0AFD82FF1012', 16)
GY = int('07192B95FFC8DA78631011ED6B24CDD573F977A11E794811', 16)


def coords(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


def hash_points(curve, count):
    points = []
    i = 0
    while len(points) < count:
        digest = hashlib.sha256(('p192-s4-base-20261123:%d' % i).encode()).digest()
        x = int.from_bytes(digest, 'big') % P
        i += 1
        if not curve.is_x_coord(x):
            continue
        point = curve.lift_x(x)
        if int(point[1]) & 1:
            point = -point
        if point not in points and -point not in points:
            points.append(point)
    return points


def s3(u, v, w, a, b):
    return ((u-v)**2*w**2 - 2*((u+v)*(u*v+a)+2*b)*w
            + (u*v-a)**2-4*b*(u+v))


def evaluate_poly(poly, variable):
    return sum(variable**i * poly[i] for i in range(poly.degree()+1))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=('source','identity','mapped5','joint5'),required=True)
    ap.add_argument('--query',choices=('planted','negative'),required=True)
    ap.add_argument('--depth',type=int,choices=(2,3),default=2)
    args=ap.parse_args()
    started=time.perf_counter()
    F=GF(P)
    E=EllipticCurve(F,[-3,B])
    G=E(GX,GY)
    aux=EllipticCurve(F,[1,0])
    samples=hash_points(aux,30)
    order=P+1
    torsion_order=2**args.depth
    T=next(order//torsion_order*point for point in samples
           if not ((torsion_order//2)*(order//torsion_order*point)).is_zero())
    assert (torsion_order*T).is_zero() and not ((torsion_order//2)*T).is_zero()
    aux_base=None
    for point in samples:
        fiber=[point+k*T for k in range(torsion_order)]
        if any(q.is_zero() for q in fiber): continue
        xs={int(q[0]) for q in fiber}
        if len(xs)==torsion_order and sum(bool(E.is_x_coord(F(x))) for x in xs)>=(1 if args.depth==2 else 4):
            aux_base=point
            break
    assert aux_base is not None
    roots=sorted({int((aux_base+k*T)[0]) for k in range(torsion_order)})
    Qaux=T
    maps=[]
    for j in range(args.depth):
        kernel=2**(args.depth-1-j)*Qaux
        assert not kernel.is_zero() and (2*kernel).is_zero()
        phi=kernel.curve().isogeny(kernel)
        maps.append(phi)
        Qaux=phi(Qaux)
    def apply(point):
        for phi in maps: point=phi(point)
        return point
    target_aux=apply(aux_base)
    assert not target_aux.is_zero()
    c=target_aux[0]
    assert all(apply(aux_base+k*T)==target_aux for k in range(torsion_order))
    funcs=[phi.x_rational_map() for phi in maps]
    nums=[f.numerator() for f in funcs]
    dens=[f.denominator() for f in funcs]
    assert all(n.gcd(d).degree()==0 for n,d in zip(nums,dens))
    composed=funcs[0]
    for n,d in zip(nums[1:],dens[1:]):
        composed=evaluate_poly(n,composed)/evaluate_poly(d,composed)
    fiber_polynomial=(composed-c).numerator()
    root_polynomial=prod(nums[0].parent().gen()-F(k) for k in roots)
    assert fiber_polynomial.monic()==root_polynomial.monic()
    rational_points=[]
    for x in roots:
        if E.is_x_coord(F(x)):
            p=E.lift_x(F(x))
            rational_points.extend([p,-p])
    assert rational_points
    chosen=[rational_points[2*(i % (len(rational_points)//2))] for i in range(4)]
    Rplanted=sum(chosen,E(0))
    a,b=71,83
    Q=int(ZZ(b).inverse_mod(R))*(Rplanted-a*G)
    rng=random.Random(20261124)
    na,nb=rng.randrange(R),rng.randrange(1,R)
    Rnegative=na*G+nb*Q
    point=Rplanted if args.query=='planted' else Rnegative
    pairset={p+q for p,q in itertools.product(rational_points,repeat=2)}
    truth=any(point-pair in pairset for pair in pairset)
    assert truth == (args.query=='planted') and not point.is_zero()
    names=['x1','x2','x3','x4']
    if args.mode in ('source','joint5'): names += ['u','v']
    names += ['w%d_%d'%(level,i) for level in range(1,args.depth) for i in range(1,5)]
    if args.mode in ('identity','mapped5','joint5'): names += ['z1','z2','z3','z4','u5','v5']
    ring=PolynomialRing(F,names=names,order='degrevlex')
    V=dict(zip(names,ring.gens()))
    x1,x2,x3,x4=(V['x%d'%i] for i in range(1,5))
    aa,bb=E.a4(),E.a6()
    equations=[]
    if args.mode in ('source','joint5'):
        u,v=V['u'],V['v']
        equations.extend((s3(x1,x2,u,aa,bb),s3(x3,x4,v,aa,bb),
                          s3(u,v,point[0],aa,bb)))
    for i,x in enumerate((x1,x2,x3,x4),1):
        values=[x]+[V['w%d_%d'%(level,i)] for level in range(1,args.depth)]+[c]
        for j in range(args.depth):
            equations.append(evaluate_poly(nums[j],values[j])-values[j+1]*evaluate_poly(dens[j],values[j]))
    horizontal_seconds=0
    map_degree=None
    if args.mode in ('identity','mapped5','joint5'):
        t=time.perf_counter()
        if args.mode=='identity':
            h=lambda p:p
            H=E
            poly=PolynomialRing(F,'X')
            hn,hd=poly.gen(),poly.one()
            map_degree=1
        else:
            h=E.isogenies_prime_degree(5)[0]
            H=h.codomain()
            hn,hd=h.x_rational_map().numerator(),h.x_rational_map().denominator()
            map_degree=5
        horizontal_seconds=time.perf_counter()-t
        assert hn.gcd(hd).degree()==0
        image=h(point)
        assert not image.is_zero()
        for i,x in enumerate((x1,x2,x3,x4),1):
            equations.append(evaluate_poly(hn,x)-V['z%d'%i]*evaluate_poly(hd,x))
        z1,z2,z3,z4=(V['z%d'%i] for i in range(1,5))
        u5,v5=V['u5'],V['v5']
        equations.extend((s3(z1,z2,u5,H.a4(),H.a6()),
                          s3(z3,z4,v5,H.a4(),H.a6()),
                          s3(u5,v5,image[0],H.a4(),H.a6())))
    if args.query=='planted':
        pair0,pair1=chosen[0]+chosen[1],chosen[2]+chosen[3]
        assert not pair0.is_zero() and not pair1.is_zero()
        W={'x%d'%i:p[0] for i,p in enumerate(chosen,1)}
        if args.mode in ('source','joint5'): W.update(u=pair0[0],v=pair1[0])
        for i,p in enumerate(chosen,1):
            value=p[0]
            for level in range(1,args.depth):
                value=funcs[level-1](value)
                W['w%d_%d'%(level,i)]=value
        if args.mode in ('identity','mapped5','joint5'):
            W.update({'z%d'%i:h(p)[0] for i,p in enumerate(chosen,1)})
            hp0,hp1=h(pair0),h(pair1)
            assert not hp0.is_zero() and not hp1.is_zero()
            W.update(u5=hp0[0],v5=hp1[0])
        witness=[W[name] for name in names]
        assert all(not eq(*witness) for eq in equations)
    setup=time.perf_counter()-started
    print(json.dumps({'event':'prepared','mode':args.mode,'query':args.query,'depth':args.depth,
                      'auxiliary_curve':'y^2=x^3+x','aux_point_order':torsion_order,
                      'roots':roots,'target_curve_liftable_x_count':len(rational_points)//2,
                      'Q':coords(Q),'query_point':coords(point),
                      'coefficients':[a,b] if args.query=='planted' else [na,nb],
                      'planted_terms':[coords(p) for p in chosen] if args.query=='planted' else None,
                      'truth':truth,'variables':len(names),'equations':len(equations),
                      'horizontal_degree':map_degree,
                      'horizontal_setup_seconds':horizontal_seconds,
                      'setup_seconds':setup,'scope':'planted positive and seeded negative; algebraic SAT only, no full IC'}),flush=True)
    started=time.perf_counter()
    basis=ring.ideal(equations).groebner_basis()
    elapsed=time.perf_counter()-started
    sat=ring.one() not in basis
    print(json.dumps({'event':'solved','mode':args.mode,'query':args.query,
                      'sat_over_algebraic_closure':sat,'point_truth':truth,
                      'groebner_seconds':elapsed,'basis_polynomials':len(basis),
                      'basis_monomials':sum(len(f.monomials()) for f in basis),
                      'max_basis_degree':max(int(f.total_degree()) for f in basis)}),flush=True)

if __name__=='__main__':main()
