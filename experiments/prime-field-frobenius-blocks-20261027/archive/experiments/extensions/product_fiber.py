"""Product-fiber solver: no multivariate elimination or Groebner basis.

If x_i are in alpha*mu_B, their product is in alpha^3*mu_B. Fixing
the product z gives the conic
  X(u+X)^2 - 2Y(u+X)w + (X^2+A)w^2 = z,
or (X(u+X)-Yw)^2 - b*w^2 = X*z.
Parametrize this conic and retain the squaring composition in a cubic
quotient over a univariate polynomial ring.
"""
from pathlib import Path
import random
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flint import nmod_poly
from core import sqrt_mod,q_coefficients,decode_cubic


def eval_poly(poly,t,p):
    return int(poly(t)) % p


def square_cubic(r,q,cache):
    a,b,c=r
    q0,q1,q2=q
    v20,v21,v22=cache
    aa,bb,cc=a*a,b*b,c*c
    ab,ac,bc=2*a*b,2*a*c,2*b*c
    return [aa-bc*q0+cc*v20,
            ab-bc*q1+cc*v21,
            bb+ac-bc*q2+cc*v22]


class ProductFiberSolver:
    def __init__(self,E,B,alpha=1,seed=20261029):
        start=time.perf_counter()
        self.E,self.p,self.B,self.alpha=E,E.p,B,alpha%E.p
        self.rng=random.Random(seed)
        p=E.p
        assert E.b and p>3 and B>=4 and B&(B-1)==0 and (p-1)%B==0 and self.alpha
        self.generator_trials=0
        while True:
            self.generator_trials+=1
            self.g=pow(self.rng.randrange(1,p),(p-1)//B,p)
            if pow(self.g,B//2,p)!=1:break
        self.c=pow(self.alpha,B,p)
        self.beta=sqrt_mod(E.b,p)
        self.norm_trials=0
        self.norm_g=self.norm_point(self.g) if self.beta is None else None
        self.setup_s=time.perf_counter()-start

    def norm_point(self,n):
        """A point of h^2-b*w^2=n; expected O(1) trials for nonzero n."""
        p,b=self.p,self.E.b
        assert n%p and self.beta is None
        while True:
            w=self.rng.randrange(p)
            h=sqrt_mod(n+b*w*w,p)
            self.norm_trials+=1
            if h is not None:
                assert (h*h-b*w*w-n)%p==0
                return h,w

    def parameters(self,R,z,base=None):
        p,A,b=self.p,self.E.a,self.E.b
        X,Y=R
        T=nmod_poly([0,1],p)
        one=nmod_poly([1],p)
        exceptional=[]
        if X==0:
            # w=T, u=(A*T^2-z)/(2Y*T).
            D=T
            W=T*T
            U=(A*T*T-z)*pow(2*Y,-1,p)
        elif self.beta is not None:
            D=T
            H=(T*T+X*z)*pow(2,-1,p)
            W=(T*T-X*z)*pow(2*self.beta,-1,p)
            U=(H+Y*W)*pow(X,-1,p)-X*D
        else:
            h,w=base
            D=one-b*T*T
            H=h*(one+b*T*T)+2*b*w*T
            W=w*(one+b*T*T)+2*h*T
            U=(H+Y*W)*pow(X,-1,p)-X*D
            exceptional=[((-h-Y*w)*pow(X,-1,p)-X,-w%p)]
        return U,W,D,exceptional

    def scalar_candidate(self,R,u,w):
        p=self.p
        u,w=u%p,w%p
        if w==0:return None
        q=nmod_poly(q_coefficients(self.E,R,u,w),p)
        T=nmod_poly([0,1],p)
        if T.pow_mod(self.B,q)!=nmod_poly([self.c],p):return None
        roots=[int(x) for x,m in q.roots() if m==1]
        return decode_cubic(self.E,R,u,w,roots)

    def solve(self,R):
        started=time.perf_counter()
        p,B,b,A=self.p,self.B,self.E.b,self.E.a
        X,Y=R
        assert Y and b
        norm_before=self.norm_trials
        one=nmod_poly([1],p);zero=nmod_poly([],p);T=nmod_poly([0,1],p)
        z=pow(self.alpha,3,p)
        norm_base=self.norm_point(X*z%p) if X and self.beta is None else None
        relations=set()
        construction_s=0;compose_s=0;root_s=0;verify_s=0
        max_degree=0;fibers_with_roots=0;parameter_roots=0
        exceptional_relations=0
        for fiber in range(B):
            start=time.perf_counter()
            U,W,D,exceptional=self.parameters(R,z,norm_base)
            delta=D*D
            q2=X*delta+2*U*D-W*W
            q1=(-X*X*delta-X*W*W+2*Y*W*D+U*U)*delta
            q0=-z*delta**3
            q=[q0,q1,q2]
            cache=[q2*q0,q2*q1-q0,q2*q2-q1]
            construction_s+=time.perf_counter()-start
            start=time.perf_counter()
            r=[zero,one,zero]
            delta_power=delta
            for _ in range(B.bit_length()-1):
                r=square_cubic(r,q,cache)
                delta_power=delta_power*delta_power
            r[0]-=self.c*delta_power
            max_degree=max(max_degree,*(int(f.degree()) for f in r))
            common=r[0].gcd(r[1]).gcd(r[2])
            compose_s+=time.perf_counter()-start
            start=time.perf_counter()
            if common.is_zero():raise RuntimeError('Positive-dimensional fiber')
            if common.degree()>0:
                common=common.gcd(T.pow_mod(p,common)-T)
                denominator=common.gcd(D)
                common=common//denominator
            roots=common.roots() if common.degree()>0 else []
            fibers_with_roots+=bool(roots);parameter_roots+=len(roots)
            root_s+=time.perf_counter()-start
            start=time.perf_counter()
            for t,_ in roots:
                t=int(t)
                inv=pow(eval_poly(D,t,p),-1,p)
                u=eval_poly(U,t,p)*inv%p
                w=eval_poly(W,t,p)*inv%p
                rel=self.scalar_candidate(R,u,w)
                if rel is None:raise RuntimeError(('Spurious fiber solution',z,t,u,w))
                relations.add(rel)
            for u,w in exceptional:
                rel=self.scalar_candidate(R,u,w)
                if rel is not None:
                    exceptional_relations+=1
                    relations.add(rel)
            verify_s+=time.perf_counter()-start
            z=z*self.g%p
            if norm_base is not None:
                h,w=norm_base;hh,ww=self.norm_g
                norm_base=((h*hh+b*w*ww)%p,(h*ww+w*hh)%p)
                assert (norm_base[0]**2-b*norm_base[1]**2-X*z)%p==0
        return {'relations':relations,'online_s':time.perf_counter()-started,
                'construction_s':construction_s,'compose_gcd_s':compose_s,
                'parameter_roots_s':root_s,'verification_s':verify_s,
                'fibers':B,'fibers_with_roots':fibers_with_roots,
                'parameter_roots':parameter_roots,'max_polynomial_degree':max_degree,
                'exceptional_relations':exceptional_relations,
                'extra_norm_trials':self.norm_trials-norm_before}
