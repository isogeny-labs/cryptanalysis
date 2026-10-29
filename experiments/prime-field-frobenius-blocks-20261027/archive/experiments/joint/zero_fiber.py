"""Zero-sum triples in a coordinate coset, without global elimination.

The line y=m*x+n gives q(T)=T^3-m^2*T^2+(A-2mn)*T+b-n^2.
Fixing z=x1*x2*x3 in alpha^3*mu_B fixes n^2=b+z. One n per
sign pair suffices modulo simultaneous negation of the three points.
All membership computations follow binary powering in a cubic quotient.
"""
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'extensions'))
from flint import nmod_poly
from core import canonical,sqrt_mod
from product_fiber import square_cubic


def prime_factors(n):
    factors=[];d=2
    while d*d<=n:
        if n%d==0:
            factors.append(d)
            while n%d==0:n//=d
        d+=1
    if n>1:factors.append(n)
    return factors


def coset(p,B,alpha=1):
    assert B>=3 and (p-1)%B==0 and alpha%p
    factors=prime_factors(B)
    for h in range(2,p):
        g=pow(h,(p-1)//B,p)
        if all(pow(g,B//d,p)!=1 for d in factors):break
    else:raise ValueError('No generator')
    xs=[];x=alpha%p
    for _ in range(B):xs.append(x);x=x*g%p
    assert x==alpha%p and len(set(xs))==B
    return g,sorted(xs)


def canonical_pm(E,points):
    return min(canonical(points),canonical(E.neg(P) for P in points))


def times_T(r,q):
    a,b,c=r;q0,q1,q2=q
    return [-c*q0,a-c*q1,b-c*q2]


class ZeroFiberSolver:
    def __init__(self,E,B,alpha=1,generator=None,composition='quotient'):
        cpu=time.process_time();wall=time.perf_counter()
        self.E,self.p,self.B,self.alpha=E,E.p,B,alpha%E.p
        assert E.p>3 and B>=3 and (E.p-1)%B==0 and self.alpha
        assert composition in ['quotient','symmetric']
        if composition=='symmetric':assert B&(B-1)==0
        self.composition=composition
        self.g=generator if generator is not None else coset(E.p,B,self.alpha)[0]
        assert pow(self.g,B,E.p)==1
        assert all(pow(self.g,B//d,E.p)!=1 for d in prime_factors(B))
        self.c=pow(self.alpha,B,E.p)
        self.setup_cpu_s=time.process_time()-cpu
        self.setup_wall_s=time.perf_counter()-wall

    def solve(self):
        cpu=time.process_time();wall=time.perf_counter()
        E,p,B=self.E,self.p,self.B
        one=nmod_poly([1],p);zero=nmod_poly([],p);T=nmod_poly([0,1],p)
        relations=set();witnesses=[]
        max_degree=0;intercepts=0;parameter_roots=0;horizontal=0;zero_intercepts=0
        compose_cpu=root_cpu=verify_cpu=0.0
        z=pow(self.alpha,3,p)
        for _ in range(B):
            start=time.process_time()
            n=sqrt_mod(E.b+z,p)
            if n is None:
                compose_cpu+=time.process_time()-start
                z=z*self.g%p
                continue
            intercepts+=1;zero_intercepts+=n==0
            q=[nmod_poly([-z],p),nmod_poly([E.a,-2*n],p),-T*T]
            q0,q1,q2=q
            discriminant=None
            if self.composition=='quotient':
                cache=[q2*q0,q2*q1-q0,q2*q2-q1]
                residue=[zero,one,zero]
                for bit in bin(B)[3:]:
                    residue=square_cubic(residue,q,cache)
                    if bit=='1':residue=times_T(residue,q)
                    max_degree=max(max_degree,*(int(f.degree()) for f in residue))
                residue[0]-=self.c
                common=residue[0].gcd(residue[1]).gcd(residue[2])
            else:
                # Elementary symmetric functions of the powered roots.
                # s,t,v = sum(x_i), sum(x_i*x_j), product(x_i).
                # Squaring roots: (s,t,v) -> (s^2-2t,t^2-2sv,v^2).
                s,t,v=-q2,q1,z
                for _ in range(B.bit_length()-1):
                    s,t,v=s*s-2*t,t*t-2*v*s,v*v%p
                    max_degree=max(max_degree,int(s.degree()),int(t.degree()))
                assert v==pow(self.c,3,p)
                common=(s-3*self.c).gcd(t-3*self.c*self.c)
                # Powered-root characteristic equations permit repeated
                # original roots. Distinct coordinates require discriminant !=0.
                discriminant=q2*q2*q1*q1-4*q1**3-4*q2**3*q0-27*q0*q0+18*q2*q1*q0
            if common.is_zero():raise RuntimeError('Positive-dimensional slope fiber')
            compose_cpu+=time.process_time()-start
            start=time.process_time()
            if common.degree()>0:common=common.gcd(T.pow_mod(p,common)-T)
            if common.degree()>0 and discriminant is not None:
                common=common//common.gcd(discriminant)
            slopes=common.roots() if common.degree()>0 else []
            parameter_roots+=len(slopes)
            root_cpu+=time.process_time()-start
            start=time.process_time()
            for m,_ in slopes:
                m=int(m)
                cubic=nmod_poly([-z,E.a-2*n*m,-m*m,1],p)
                assert T.pow_mod(B,cubic)==nmod_poly([self.c],p)
                roots=cubic.roots()
                assert len(roots)==3 and all(mult==1 for x,mult in roots)
                points=[(int(x),(m*int(x)+n)%p) for x,mult in roots]
                assert len({x for x,y in points})==3
                assert all(E.contains(P) and pow(P[0],B,p)==self.c for P in points)
                assert E.sum(points) is None
                relation=canonical_pm(E,points)
                if relation not in relations:
                    relations.add(relation)
                    witnesses.append({'z':z,'slope':m,'intercept':n,'points':relation})
                    horizontal+=m==0
            verify_cpu+=time.process_time()-start
            z=z*self.g%p
        assert z==pow(self.alpha,3,p)
        assert max_degree<=2*B
        return {'relations':relations,'witnesses':witnesses,
                'cpu_s':time.process_time()-cpu,'wall_s':time.perf_counter()-wall,
                'compose_gcd_cpu_s':compose_cpu,'root_cpu_s':root_cpu,
                'verify_cpu_s':verify_cpu,'product_fibers':B,
                'intercept_fibers':intercepts,'parameter_roots':parameter_roots,
                'max_polynomial_degree':max_degree,'horizontal_relations':horizontal,
                'zero_intercept_fibers':zero_intercepts}
