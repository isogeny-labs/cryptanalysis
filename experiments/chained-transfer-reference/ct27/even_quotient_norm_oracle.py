#!/usr/bin/env python3
"""Independent F_101 elliptic quotient norm certificate; no project imports.

Tests the map (x,y)->(x^2,y) for y^2=x^6+a*x^4+b*x^2+c.
All public toy arithmetic and exact finite-field checks, no timings.
"""
from itertools import combinations

P = 101
D = 2  # nonsquare in F_101
CUBICS = ((6,13,56), (26,42,68))

def inv(x):
    assert x % P
    return pow(x, P - 2, P)

def fp2(a, b=0):
    return (a % P, b % P)

def a2(x, y):
    return fp2(x[0]+y[0], x[1]+y[1])

def n2(x):
    return fp2(-x[0], -x[1])

def s2(x,y):
    return a2(x,n2(y))

def m2(x, y):
    return fp2(x[0]*y[0]+D*x[1]*y[1], x[0]*y[1]+x[1]*y[0])

def i2(x):
    den=inv((x[0]*x[0]-D*x[1]*x[1])%P)
    return fp2(x[0]*den,-x[1]*den)

def d2(x,y):
    return m2(x,i2(y))

def p2(x,n):
    z=fp2(1)
    while n:
        if n & 1: z=m2(z,x)
        x=m2(x,x)
        n>>=1
    return z

def b2(x):
    assert x[1] == 0, x
    return x[0]

def cval(x,a,b,c):
    # genus-2 sextic, over F_101^2
    x2=m2(x,x); x4=m2(x2,x2)
    return a2(a2(m2(x4,x2),m2(fp2(a),x4)),a2(m2(fp2(b),x2),fp2(c)))

def elliptic_add(Pt,Qt,a,b,c,add,sub,mul,divide,zero):
    if Pt is None:return Qt
    if Qt is None:return Pt
    x,y=Pt; u,v=Qt
    if x == u and add(y,v) == zero: return None
    if x == u:
        if y == zero:return None
        slope=divide(add(add(mul(x,x),mul(x,x)),add(mul(x,x),add(mul(a,add(x,x)),b))),add(y,y))
    else:
        slope=divide(sub(v,y),sub(u,x))
    xout=sub(sub(sub(mul(slope,slope),a),x),u)
    yout=sub(mul(slope,sub(x,xout)),y)
    return (xout,yout)

def add_f(x,y):return (x+y)%P

def sub_f(x,y):return (x-y)%P

def mul_f(x,y):return x*y%P

def div_f(x,y):return x*inv(y)%P

def ec_f(Pt,Qt,a,b,c):
    return elliptic_add(Pt,Qt,a,b,c,add_f,sub_f,mul_f,div_f,0)

def ec2(Pt,Qt,a,b,c):
    return elliptic_add(Pt,Qt,fp2(a),fp2(b),fp2(c),a2,s2,m2,d2,fp2(0))

def ell_valid(Pt,a,b,c):
    if Pt is None:return True
    x,y=Pt
    return y*y%P == (pow(x,3,P)+a*x*x+b*x+c)%P

def norm_quad(s,t,v0,v1,a,b,c):
    """Push u=x^2+s*x+t, v=v0+v1*x to E: Y^2=U^3+aU^2+bU+c."""
    if s:
        m=(-v1*inv(s))%P
        n=(v0+m*t)%P
        S=(s*s-2*t)%P
        U=(m*m-a-S)%P
        Y=(-m*U-n)%P
        out=(U,Y)
    elif v1:
        assert v0 == 0
        out=None
    else:
        Q=((-t)%P,v0)
        assert ell_valid(Q,a,b,c)
        out=ec_f(Q,Q,a,b,c)
    assert ell_valid(out,a,b,c)
    return out

def reciprocal_point(x,y,c):
    if x == 0:return None
    x2=x*x%P
    return (c*inv(x2)%P,c*y*inv(x*x2%P)%P)

def reciprocal_point2(x,y,c):
    if x==fp2(0):return None
    xx=m2(x,x)
    return (d2(fp2(c),xx),d2(m2(fp2(c),y),m2(xx,x)))

def rec_ec(Pt,Qt,a,b,c):
    return ec_f(Pt,Qt,b,a*c%P,c*c%P)

def rec_ec2(Pt,Qt,a,b,c):
    return ec2(Pt,Qt,b,a*c%P,c*c%P)

def rec_norm_quad(s,t,v0,v1,a,b,c):
    """Reciprocal quotient V=c/x², Z=c*y/x³. Finite degree-two support."""
    if not t:
        if not s:return None  # two points supported at x=0
        return reciprocal_point((-s)%P,(v0-v1*s)%P,c)
    sp=s*inv(t)%P
    tp=inv(t)
    z0=c*tp*(v0*sp-v1)%P
    z1=c*(v0*(sp*sp-tp)-v1*sp)%P
    if sp:
        m=(-z1*inv(sp)*inv(c))%P
        n=(z0+m*c*tp)%P
        S=c*(sp*sp-2*tp)%P
        V=(m*m-b-S)%P
        Z=(-m*V-n)%P
        result=(V,Z)
    elif z1:
        assert z0 == 0
        result=None
    else:
        Q=((-c*tp)%P,z0)
        result=rec_ec(Q,Q,a,b,c)
    if result is not None:
        V,Z=result
        assert Z*Z%P==(V**3+b*V*V+a*c*V+c*c)%P
    return result

def balanced_norm(degree, plus, data, a,b,c):
    """Full effective degree-two class, K=infty+ + infty-; no field extensions."""
    assert 0 <= plus <= 2-degree
    if degree==0:
        even=None;rec=None
    elif degree==1:
        x,y=data
        even=(x*x%P,y)
        rec=reciprocal_point(x,y,c)
    else:
        s,t,v0,v1=data
        even=norm_quad(s,t,v0,v1,a,b,c)
        rec=rec_norm_quad(s,t,v0,v1,a,b,c)
    # Both source infinities map to elliptic O under the even quotient.
    # The reciprocal quotient sends them to (0,+c),(0,-c).
    delta=2*plus+degree-2
    Tplus=(0,c)
    if delta<0:
        Tplus=(0,(-c)%P)
    for _ in range(abs(delta)):
        rec=rec_ec(rec,Tplus,a,b,c)
    return even,rec

def remainder_valid(s,t,v0,v1,a,b,c):
    # Compute f(x)-v(x)^2 modulo x^2+s*x+t over Fp, independent of norm evaluator.
    def mul_ring(z,w):
        c0=z[0]*w[0] -t*z[1]*w[1]
        c1=z[0]*w[1]+w[0]*z[1]-s*z[1]*w[1]
        return(c0%P,c1%P)
    r1=(0,1); r2=mul_ring(r1,r1);r4=mul_ring(r2,r2);r6=mul_ring(r4,r2)
    f=((r6[0]+a*r4[0]+b*r2[0]+c)%P,(r6[1]+a*r4[1]+b*r2[1])%P)
    vv=mul_ring((v0,v1),(v0,v1))
    return f==vv

def run(a,b,c):
    fp_roots={z*z%P:z for z in range(P)}
    sqrts={}
    for i in range(P):
        for j in range(P):
            z=fp2(i,j)
            sqrts.setdefault(m2(z,z),z)
    assert len(sqrts)==(P*P+1)//2
    assert pow(D,(P-1)//2,P)==P-1
    affine=[(x,y) for x in range(P) for y in range(P)
       if y*y%P==(pow(x,6,P)+a*pow(x,4,P)+b*x*x+c)%P]
    counts={"affine":len(affine),"degree1":0,"split":0,"nonsplit":0,
            "repeated":0,"opposite_support":0,"zero_x":0,"zero_s_split":0,"zero_s_nonsplit":0}
    infplus=(0,c)
    assert rec_ec(infplus,(0,-c%P),a,b,c) is None
    seen=set()
    for plus in range(3):
        got=balanced_norm(0,plus,(),a,b,c)
        expected=None
        for _ in range(plus):expected=rec_ec(expected,infplus,a,b,c)
        for _ in range(2-plus):expected=rec_ec(expected,(0,-c%P),a,b,c)
        assert got == (None,expected)
        assert (0,plus) not in seen
        seen.add((0,plus))
    for x,y in affine:
        Q=(x*x%P,y)
        assert ell_valid(Q,a,b,c)
        counts["degree1"]+=1
        r=reciprocal_point(x,y,c)
        for plus in (0,1):
            got=balanced_norm(1,plus,(x,y),a,b,c)
            expected=rec_ec(r,infplus if plus else (0,-c%P),a,b,c)
            assert got==(Q,expected)
            assert (1,x,y,plus) not in seen
            seen.add((1,x,y,plus))
        if x==0:counts["zero_x"]+=1
    for (x,y),(x2,y2) in combinations(affine,2):
        if x==x2:
            assert y == -y2%P
            counts["opposite_support"]+=1
            continue
        v1=((y-y2)*inv((x-x2)%P))%P
        v0=(y-v1*x)%P
        s=(-(x+x2))%P;t=x*x2%P
        assert remainder_valid(s,t,v0,v1,a,b,c)
        got=norm_quad(s,t,v0,v1,a,b,c)
        expected=ec_f((x*x%P,y),(x2*x2%P,y2),a,b,c)
        assert got == expected,(s,t,v0,v1,got,expected)
        assert (2,s,t,v0,v1) not in seen
        seen.add((2,s,t,v0,v1))
        assert balanced_norm(2,0,(s,t,v0,v1),a,b,c)==(got,rec_norm_quad(s,t,v0,v1,a,b,c))
        recgot=rec_norm_quad(s,t,v0,v1,a,b,c)
        recexpected=rec_ec(reciprocal_point(x,y,c),reciprocal_point(x2,y2,c),a,b,c)
        assert recgot==recexpected,(s,t,v0,v1,recgot,recexpected)
        counts["split"]+=1
        if not s:counts["zero_s_split"]+=1
    for x,y in affine:
        if y==0:continue
        fprime=(6*pow(x,5,P)+4*a*pow(x,3,P)+2*b*x)%P
        v1=(fprime*inv(2*y%P))%P
        v0=(y-v1*x)%P
        s=(-2*x)%P;t=x*x%P
        assert remainder_valid(s,t,v0,v1,a,b,c)
        got=norm_quad(s,t,v0,v1,a,b,c)
        expected=ec_f((x*x%P,y),(x*x%P,y),a,b,c)
        assert got==expected,(x,y,got,expected)
        assert (2,s,t,v0,v1) not in seen
        seen.add((2,s,t,v0,v1))
        assert balanced_norm(2,0,(s,t,v0,v1),a,b,c)==(got,rec_norm_quad(s,t,v0,v1,a,b,c))
        recgot=rec_norm_quad(s,t,v0,v1,a,b,c)
        recpoint=reciprocal_point(x,y,c)
        recexpected=rec_ec(recpoint,recpoint,a,b,c)
        assert recgot==recexpected,(x,y,recgot,recexpected)
        counts["repeated"]+=1
    # All 5050 irreducible monic quadratics x^2+s*x+t.
    tested=0
    for s in range(P):
        for t in range(P):
            disc=(s*s-4*t)%P
            if disc==0 or pow(disc,(P-1)//2,P)!=P-1:continue
            tested+=1
            z=fp_roots.get(disc*inv(D)%P)
            # A nonsquare discriminant divided by nonsquare 2 has a base-field square root.
            assert z is not None and z*z*D%P==disc
            r=fp2((-s*inv(2))%P,z*inv(2)%P)
            yroot=sqrts.get(cval(r,a,b,c))
            if yroot is None:continue
            rbar=fp2(r[0],-r[1])
            for y in (yroot,n2(yroot)):
                ybar=fp2(y[0],-y[1])
                v1=b2(d2(s2(y,ybar),s2(r,rbar)))
                v0=b2(s2(y,m2(fp2(v1),r)))
                assert remainder_valid(s,t,v0,v1,a,b,c)
                got=norm_quad(s,t,v0,v1,a,b,c)
                Q=(m2(r,r),y)
                Qbar=(m2(rbar,rbar),ybar)
                assert m2(y,y)==cval(r,a,b,c)
                assert m2(ybar,ybar)==cval(rbar,a,b,c)
                ext=ec2(Q,Qbar,a,b,c)
                expected=None if ext is None else (b2(ext[0]),b2(ext[1]))
                assert got==expected,(s,t,v0,v1,got,expected)
                assert (2,s,t,v0,v1) not in seen
                seen.add((2,s,t,v0,v1))
                assert balanced_norm(2,0,(s,t,v0,v1),a,b,c)==(got,rec_norm_quad(s,t,v0,v1,a,b,c))
                recgot=rec_norm_quad(s,t,v0,v1,a,b,c)
                extrec=rec_ec2(reciprocal_point2(r,y,c),reciprocal_point2(rbar,ybar,c),a,b,c)
                recexpected=None if extrec is None else (b2(extrec[0]),b2(extrec[1]))
                assert recgot==recexpected,(s,t,v0,v1,recgot,recexpected)
                counts["nonsplit"]+=1
                if not s:counts["zero_s_nonsplit"]+=1
    assert len(seen)==12317, (len(seen),counts)
    counts["full_balanced_classes"]=len(seen)
    assert tested==P*(P-1)//2
    counts["irreducible_u_examined"]=tested
    assert counts["nonsplit"]>0 and counts["repeated"]>0 and counts["zero_s_nonsplit"]>0
    return counts

if __name__=="__main__":
    # Fails closed even when assert statements disabled.
    import sys
    if not __debug__:sys.exit("Refuse optimized Python: correctness assertions disabled")
    for cubic in CUBICS:
        print("PASS",cubic,run(*cubic))
