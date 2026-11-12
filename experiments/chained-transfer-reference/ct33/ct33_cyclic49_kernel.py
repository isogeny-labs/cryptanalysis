#!/usr/bin/env python3
"""CT33: prime-field x-only construction of the selected cyclic-49 kernel.

Independent stdlib-only arithmetic; published F101 elliptic inputs from
crypto PR3877 and cryptanalysis PR1492, not an imported producer evaluator.
All checks are unsigned development evidence [pcc:unverified].
"""
from dataclasses import dataclass

P = 101

def poly(a):
    a = [int(x) % P for x in a]
    while len(a)>1 and a[-1]==0:
        a.pop()
    return tuple(a) if a else (0,)

def add(a,b):
    return poly([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
                 for i in range(max(len(a),len(b)))])
def minus(a): return poly([-c for c in a])
def sub(a,b): return add(a,minus(b))
def scale(a,k): return poly([k*t for t in a])
def mul(a,b):
    t=[0]*(len(a)+len(b)-1)
    for i,c in enumerate(a):
        for j,d in enumerate(b): t[i+j]+=c*d
    return poly(t)
def square(a): return mul(a,a)
def power(a,n):
    r=(1,)
    while n:
        if n&1:r=mul(r,a)
        a=square(a);n>>=1
    return r
def derivative(a):return poly([i*a[i] for i in range(1,len(a))])
def divmodp(a,b):
    a=list(poly(a));b=poly(b)
    if b==(0,):raise ZeroDivisionError
    q=[0]*max(1,len(a)-len(b)+1)
    inv=pow(b[-1],-1,P)
    while len(a)>=len(b) and a!=[0]:
        d=len(a)-len(b);c=a[-1]*inv%P;q[d]=c
        for i,v in enumerate(b):a[d+i]=(a[d+i]-c*v)%P
        while len(a)>1 and a[-1]==0:a.pop()
    return poly(q),poly(a)
def modp(a,b):return divmodp(a,b)[1]
def gcdp(a,b):
    while b!=(0,):a,b=b,modp(a,b)
    return scale(a,pow(a[-1],-1,P))
def powmodp(a,n,m):
    out=(1,)
    while n:
        if n&1:out=modp(mul(out,a),m)
        a=modp(square(a),m);n>>=1
    return out

def velu_xmap(a,b,h):
    """Direct pair-sum rational x Vélu: N/h², with N monic of degree seven."""
    h=poly(h); f=poly((b,a,0,1));fp=derivative(f);hp=derivative(h)
    D=square(h)
    # Sum of the roots of the monic cubic h.
    s1=-h[2]
    N=add(sub(mul(poly((-2*s1,7)),D),scale(mul(mul(fp,hp),h),2)),
          scale(mul(f,sub(square(hp),mul(h,derivative(hp)))),4))
    return poly(N),D

def velu_codomain(a,b,h):
    """Symmetric sums of the three x-pairs in the order-seven kernel."""
    e1=-h[2]%P; e2=h[1]%P; e3=-h[0]%P
    s2=(e1*e1-2*e2)%P
    s3=(e1**3-3*e1*e2+3*e3)%P
    v=(2*(3*s2+3*a))%P
    w=(2*(5*s3+3*a*e1+6*b))%P
    return ((a-5*v)%P,(b-7*w)%P)

def equation(a,b,aa,bb,N,D):
    f=poly((b,a,0,1));d=derivative(N);dd=derivative(D)
    W=sub(mul(d,D),mul(N,dd))
    lhs=mul(f,square(W))
    rhs=mul(D,add(add(power(N,3),scale(mul(N,square(D)),aa)),scale(power(D,3),bb)))
    return lhs==rhs

def homogenized(h,N,D):
    """Substitute rational X=N/D into a polynomial of arbitrary degree."""
    m=len(h)-1
    out=(0,)
    # Entire expression has denominator D^m, including the leading term.
    ns=[(1,)];ds=[(1,)]
    for _ in range(m):
        ns.append(mul(ns[-1],N))
        ds.append(mul(ds[-1],D))
    for i,coef in enumerate(h):
        out=add(out,scale(mul(ns[i],ds[m-i]),coef))
    return out

def lift_poly(h,N,D):
    """Homogeneous pullback of a monic cubic h through X=N/D."""
    return homogenized(h,N,D)

def check(ok, message):
    if not ok:
        raise ValueError(message)

def degrees_report(F, require_split=True):
    x=poly((0,1));n=len(F)-1
    f=x;out={}
    for d in range(1,n+1):
        f=powmodp(f,P,F)
        out[d]=len(gcdp(F,sub(f,x)))-1
    if require_split:
        check(f==x, 'all support x-coordinates must be F101^n-rational')
    check(gcdp(F,derivative(F))==(1,), 'no repeated support coordinates')
    return out

@dataclass(frozen=True)
class Case:
    tag:str; a:int;b:int;card:int; h0:tuple; e1:tuple; h1:tuple;dual:tuple
    expected_e2:tuple; expected_frob:int; expected_degree:int

CASES=(
    Case('E109',1,46,109,(72,100,35,1),(26,58),(99,94,75,1),
         (58,26,58,1),(59,27),33,21),
    Case('E113',44,21,113,(59,46,8,1),(69,50),(53,19,40,1),
         (29,88,45,1),(23,7),27,7),
)

def audit(c):
    check(velu_codomain(c.a,c.b,c.h0)==c.e1, 'first isogeny codomain')
    N,D=velu_xmap(c.a,c.b,c.h0)
    check(len(N)==8 and len(D)==7 and D==square(c.h0), 'normalized first Vélu map')
    check(gcdp(N,D)==(1,), 'Vélu map must be reduced')
    check(equation(c.a,c.b,*c.e1,N,D), 'global rational first map identity')
    check(not equation(c.a,c.b,c.e1[0],(c.e1[1]+1)%P,N,D), 'wrong codomain accepted')
    check(c.h1!=c.dual, 'backtracking kernel mistakenly selected')
    N2,D2=velu_xmap(*c.e1,c.h1)
    E2=velu_codomain(*c.e1,c.h1)
    check(E2==c.expected_e2, 'second codomain differs from pinned fixture')
    check(equation(*c.e1,*E2,N2,D2), 'global rational second map identity')
    check(not equation(*c.e1,E2[0],(E2[1]+1)%P,N2,D2), 'wrong second codomain accepted')
    H=lift_poly(c.h1,N,D)
    check(len(H)==22 and H[-1]==1, 'primitive support degree21 monic')
    check(gcdp(H,c.h0)==(1,), 'primitive support intersects first kernel')
    check(gcdp(H,D)==(1,), 'kernel support on pole')
    K=mul(c.h0,H)
    check(len(K)==25 and K[-1]==1, 'composite kernel degree24')
    # Analytic denominator of composite x map must be (h0 H)^2.
    # The unreduced denominator D0 * D1(N0/D0) has degree48 and is K².
    Dcomp=mul(D,lift_poly(c.h1,N,D))
    Dcomp=mul(Dcomp,lift_poly(c.h1,N,D)) # this is D0 * H^2 = K^2
    check(Dcomp==square(K), 'composite 49-isogeny pole divisor')
    Ncomp=homogenized(N2,N,D)
    check(len(Ncomp)==50 and Ncomp[-1]==1, 'composite map numerator degree49')
    check(gcdp(Ncomp,Dcomp)==(1,), 'composite rational map unexpectedly reduces')
    check(equation(c.a,c.b,*E2,Ncomp,Dcomp), 'global composed degree49 rational map identity')
    check(not equation(c.a,c.b,E2[0],(E2[1]+1)%P,Ncomp,Dcomp),
          'wrong final degree49 codomain accepted')
    # The corresponding backtracking choice may NOT have the primitive
    # orbit structure; it selects E0[7] rather than a cyclic-49 kernel.
    back=lift_poly(c.dual,N,D)
    check(H!=back, 'backtracking pullback was identical')
    report=degrees_report(H)
    back_report=degrees_report(back,require_split=False)
    if c.tag=='E109':
        check(report[3]==0 and report[7]==0 and report[21]==21, str(report))
    else:
        check(report[1]==0 and report[7]==21, str(report))
        check(all(report[d]==0 for d in (2,3,4,5,6)), 'premature E113 fixed degree')
    # Check Frobenius orbit degree via independently counted root population.
    # For a primitive Q on selected 49-line, Frob^d x(Q) = x(Q) iff
    # Frobenius eigenvalue^d = +/- 1 mod49.
    minimal=next(i for i in range(1,43) if pow(c.expected_frob,i,49) in (1,48))
    check(minimal==c.expected_degree, 'Frobenius order mismatch')
    check(report[minimal]==21 and all(report[d]==0 for d in range(1,minimal)), 'orbit does not match eigenline')
    return dict(name=c.tag,E0=(c.a,c.b),E1=c.e1,E2=E2,
                h0=list(c.h0),h1=list(c.h1),N=list(N),D=list(D),
                composite_numerator_degree=len(Ncomp)-1,
                primitive_H=list(H),whole_K=list(K),
                fixed_degrees={d:v for d,v in report.items() if v},
                backtracking_degrees={d:v for d,v in back_report.items() if v})

def main():
    import json
    for c in CASES:
        r=audit(c)
        print(json.dumps(r,separators=(',',':')))
    print('CT33 PASS: two explicit degree24 x-only composite kernels, two global Vélu identities per chain, Frobenius orbit degrees and wrong-target/backtracking controls [pcc:unverified]')

if __name__=='__main__':main()