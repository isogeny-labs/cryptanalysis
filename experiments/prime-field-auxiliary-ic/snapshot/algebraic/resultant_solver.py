"""Structure-aware, exact two-point relation solving by quadratic norms.

This consumes the low-degree isogeny composition directly. It introduces no
Groebner variables, performs no pair-table search, and returns every verified
finite-point decomposition. An efficient product-tree solver handles the
unstructured baseline.
"""
from dataclasses import dataclass
import itertools
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parent
try:
    from flint import nmod_poly
except ImportError:
    sys.path.insert(0,str(ROOT/'vendor/python'))
    try:
        from flint import nmod_poly
    except ImportError as exc:
        raise ImportError('Install python-flint, or use vendor/python; see structure README') from exc
sys.path.insert(0,str(ROOT.parent))
from prepare import Curve
from sympy import isprime


def product_tree(polynomials,p):
    level=list(polynomials)
    if not level:return nmod_poly([1],p)
    while len(level)>1:
        level=[level[i]*level[i+1] if i+1<len(level) else level[i]
               for i in range(0,len(level),2)]
    return level[0]


@dataclass
class Membership:
    curve:dict
    encoding:str
    polynomial:object
    auxiliary:dict|None=None
    roots:tuple|None=None
    prepare_seconds:float=0


def prepare(curve,*,auxiliary=None,roots=None,encoding='chain'):
    started=time.perf_counter()
    p=int(curve['p'])
    if p<=3 or p>=2**64 or p%4!=3 or not isprime(p):
        raise ValueError('This implementation requires a prime p=3 mod 4 below 2^64')
    curve=dict(p=p,a=int(curve['a'])%p,b=int(curve['b'])%p)
    if (4*curve['a']**3+27*curve['b']**2)%p==0:raise ValueError('Singular target curve')
    x=nmod_poly([0,1],p)
    if encoding=='chain':
        if not auxiliary or auxiliary['p']!=p:raise ValueError('Auxiliary field mismatch')
        if not auxiliary['maps'] or any(step['B']%p==0 for step in auxiliary['maps']):
            raise ValueError('Nonzero B is required for every degree-two map')
        N,D=x,nmod_poly([1],p)
        for step in auxiliary['maps']:
            U=N-step['r']*D
            N,D=U*U+step['A']*U*D+step['B']*D*D,U*D
        P=N-auxiliary['terminal_c']*D
        assert P.degree()==auxiliary['root_count']
        if roots is not None:
            roots=tuple(int(v)%p for v in roots)
            if len(roots)!=P.degree() or len(set(roots))!=len(roots) or product_tree((nmod_poly([-v,1],p) for v in roots),p)!=P:
                raise ValueError('Explicit roots do not match the auxiliary membership polynomial')
    else:
        if roots is None:raise ValueError('Explicit roots required')
        roots=tuple(int(v)%p for v in roots)
        if not roots or len(set(roots))!=len(roots):raise ValueError('Distinct roots required')
        P=product_tree((nmod_poly([-v,1],p) for v in roots),p)
    return Membership(dict(curve),encoding,P,auxiliary,roots,time.perf_counter()-started)


def coefficients(curve,X):
    p,a,b=(curve[k] for k in ['p','a','b'])
    x=nmod_poly([0,1],p)
    alpha=(x-X)**2
    beta=-2*((x+X)*(X*x+a)+2*b)
    gamma=(X*x-a)**2-4*b*(x+X)
    return alpha,beta,gamma


def chain_resultant_norm_reference(model,target):
    """Res_y(S3(x,y,X), P(y)) using the isogeny circuit for P.

    In F_p(x)[y]/(alpha*y^2+beta*y+gamma), keep both homogeneous
    numerator/denominator as linear forms divided by alpha^e. Every circuit
    step doubles e and adds one. At the end e=S-1. A quadratic norm and exact
    division by alpha^(S-1) give the resultant, of degree at most 2S.
    """
    p=model.curve['p'];alpha,beta,gamma=coefficients(model.curve,target[0])
    zero,one=nmod_poly([],p),nmod_poly([1],p)
    Nu,Nv,Du,Dv=one,zero,zero,one

    def multiply(U,V):
        u,v=U;s,t=V;us=u*s
        return alpha*(u*t+v*s)-beta*us,alpha*v*t-gamma*us

    def square(U):
        u,v=U;u2=u*u
        return alpha*(2*u*v)-beta*u2,alpha*v*v-gamma*u2

    for step in model.auxiliary['maps']:
        T=(Nu-step['r']*Du,Nv-step['r']*Dv)
        TT,TD,DD=square(T),multiply(T,(Du,Dv)),square((Du,Dv))
        Nu=TT[0]+step['A']*TD[0]+step['B']*DD[0]
        Nv=TT[1]+step['A']*TD[1]+step['B']*DD[1]
        Du,Dv=TD
    u=Nu-model.auxiliary['terminal_c']*Du
    v=Nv-model.auxiliary['terminal_c']*Dv
    norm=alpha*v*v-beta*u*v+gamma*u*u
    S=model.polynomial.degree()
    result,remainder=divmod(norm,alpha**(S-1))
    if remainder:raise ArithmeticError('Quadratic norm did not divide exactly')
    assert result.degree()<=2*S
    return result


def chain_resultant(model,target):
    """Push a quadratic through each 2-isogeny, retaining only 3 coefficients.

    Q_j(z)=D*z^2-C*z+H is the weighted quadratic whose roots are the two
    isogeny images of roots of S3(x,y,X). For f(z)=u+A+B/u, u=z-r,
    the formulas below compute its exact resultant image. At the end Q_s(c)
    is Res_y(S3(x,y,X),P(y)), with no large denominator or norm division.
    """
    p=model.curve['p'];D,beta,H=coefficients(model.curve,target[0]);C=-beta
    for step in model.auxiliary['maps']:
        r,A,B=(step[k]%p for k in ['r','A','B'])
        U=H-r*C+(r*r%p)*D
        V=C-(2*r%p)*D
        BD=B*D
        newD=U*D
        newC=V*(U+BD)+(2*A%p)*newD
        difference=U-BD
        newH=difference*difference+B*(V*V)+A*newC-(A*A%p)*newD
        D,C,H=newD,newC,newH
    c=model.auxiliary['terminal_c']%p
    return H-c*C+(c*c%p)*D


def explicit_resultant(model,target):
    """The same resultant, using an efficient balanced product of quadratics."""
    p,a,b=(model.curve[k] for k in ['p','a','b']);X=target[0]
    leaves=[]
    for v in model.roots:
        c2=(v-X)**2%p
        c1=-2*(X*v*v+(X*X+a)*v+a*X+2*b)%p
        c0=((X*v-a)**2-4*b*(v+X))%p
        leaves.append(nmod_poly([c0,c1,c2],p))
    return product_tree(leaves,p)


def solve(model,target,*,keep_polynomial=False,root_plan=None):
    target=tuple(int(v)%model.curve['p'] for v in target)
    p,a,b=(model.curve[k] for k in ['p','a','b'])
    E=Curve(p,a4=a,a6=b)
    if not E.contains(target):raise ValueError('Target is not on curve')
    if root_plan is not None and root_plan.membership_polynomial!=model.polynomial:
        raise ValueError('Known-root plan does not match the membership polynomial')
    if root_plan is not None and root_plan.curve is not None and root_plan.curve!=model.curve:
        raise ValueError('Liftable-root plan was prepared for a different target curve')
    started=time.perf_counter()
    elimination_started=started
    resultant=chain_resultant(model,target) if model.encoding=='chain' else explicit_resultant(model,target)
    elimination=time.perf_counter()-elimination_started
    gcd_started=time.perf_counter()
    if root_plan is None:
        G=model.polynomial.gcd(resultant)
        gcd_degree=G.degree()
    else:
        candidates=root_plan.candidates(resultant)
        gcd_degree=len(candidates)
    gcd_seconds=time.perf_counter()-gcd_started
    extraction_started=time.perf_counter()
    if root_plan is None:candidates={int(v) for v,_ in G.roots()}
    # This also covers the leading-coefficient degeneration alpha(X)=0.
    if int(model.polynomial(target[0]))==0:candidates.add(target[0])
    relations={}
    alpha,beta,gamma=coefficients(model.curve,target[0])
    for x in candidates:
        ypoly=nmod_poly([int(gamma(x)),int(beta(x)),int(alpha(x))],p)
        if not ypoly:raise ArithmeticError('Unexpected identically zero S3 specialization')
        for yy,_ in ypoly.roots():
            y=int(yy)
            if int(model.polynomial(y))!=0:continue
            choices=[]
            for coordinate in [x,y]:
                rhs=(coordinate**3+a*coordinate+b)%p
                Y=pow(rhs,(p+1)//4,p)
                if Y*Y%p!=rhs:break
                choices.append([(coordinate,Y)] if Y==0 else [(coordinate,Y),(coordinate,-Y%p)])
            if len(choices)!=2:continue
            for P,Q in itertools.product(*choices):
                if E.add(P,Q)==target:relations[tuple(sorted([P,Q]))]=[list(P),list(Q)]
    extraction_seconds=time.perf_counter()-extraction_started
    result=dict(status='solved',engine='quadratic-resultant',encoding=model.encoding,
                elapsed_seconds=time.perf_counter()-started,elimination_seconds=elimination,
                gcd_seconds=gcd_seconds,extraction_seconds=extraction_seconds,
                root_count=model.polynomial.degree(),resultant_degree=resultant.degree(),
                gcd_degree=gcd_degree,candidates=len(candidates),relations=list(relations.values()),
                candidate_backend=('liftable-known-root-blocks' if root_plan.liftable_only else 'known-root-blocks') if root_plan else 'flint-gcd')
    if keep_polynomial:result['_resultant']=resultant
    return result


def signed_base(model,roots):
    p,a,b=(model.curve[k] for k in ['p','a','b'])
    roots=tuple(int(v)%p for v in roots)
    if roots!=model.roots:
        if len(roots)!=model.polynomial.degree() or len(set(roots))!=len(roots) or product_tree((nmod_poly([-v,1],p) for v in roots),p)!=model.polynomial:
            raise ValueError('Three-point enumeration requires the complete matching root set')
    points=[]
    for x in roots:
        rhs=(x**3+a*x+b)%p;y=pow(rhs,(p+1)//4,p)
        if y*y%p!=rhs:continue
        points.append((x,y))
        if y:points.append((x,-y%p))
    return sorted(points)


def solve_three(model,target,points,*,root_plan=None):
    """Complete 3-sum existence search with one base-point enumeration.

    For each fixed P3 solve the remaining 2-sum algebraically. The baseline
    uses precisely the same algorithm. No point-pair table is constructed.
    Returns the first relation, as needed by index calculus.
    """
    p,a,b=(model.curve[k] for k in ['p','a','b']);E=Curve(p,a4=a,a6=b)
    target=tuple(target)
    if not E.contains(target):raise ValueError('Target is not on curve')
    started=time.perf_counter();calls=0;elimination=gcd_seconds=0
    for P3 in points:
        remainder=E.add(target,E.neg(P3))
        if remainder is None:
            if not points:continue
            relation=[list(points[0]),list(E.neg(points[0])),list(P3)]
            break
        answer=solve(model,remainder,root_plan=root_plan);calls+=1
        elimination+=answer['elimination_seconds'];gcd_seconds+=answer['gcd_seconds']
        if answer['relations']:
            relation=answer['relations'][0]+[list(P3)]
            break
    else:relation=None
    if relation:
        assert all(int(model.polynomial(P[0]))==0 for P in relation)
        assert E.add(E.add(tuple(relation[0]),tuple(relation[1])),tuple(relation[2]))==target
    return dict(status='solved',engine='hybrid-three-sum-resultant',encoding=model.encoding,
                elapsed_seconds=time.perf_counter()-started,elimination_seconds=elimination,
                gcd_seconds=gcd_seconds,two_sum_calls=calls,factor_base_points=len(points),
                relations=[relation] if relation else [])
