#!/usr/bin/env python3
"""Independent coefficientwise audit of four normalized 7-isogenies over F_101.

Uses no SymPy, division-polynomial implementation, or producer isogeny code.
The source kernels/codomains are fixed public toy inputs, not rediscovered here.
All arithmetic is in polynomial rings and elliptic groups over F_101.
Scientific standing: [pcc:unverified].
"""
P = 101
CASES = (
    ('109 nondual', 26, 58, (99,94,75,1), 59,27, 109),
    ('109 backtrack',26,58, (58,26,58,1),78,72,109),
    ('113 nondual',69,50, (53,19,40,1),23,7,113),
    ('113 backtrack',69,50, (29,88,45,1),99,68,113),
)

def p(v):
    if isinstance(v,int): v=(v,)
    v=[int(a)%P for a in v]
    while len(v)>1 and v[-1]==0: v.pop()
    return tuple(v or (0,))

def add(a,b):
    a=p(a);b=p(b)
    return p([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))])

def neg(a):return p([-c for c in p(a)])
def sub(a,b):return add(a,neg(b))
def scale(a,n):return p([n*c for c in p(a)])
def mul(a,b):
    a=p(a);b=p(b);v=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):v[i+j]+=x*y
    return p(v)
def pw(a,n):
    out=p(1)
    for _ in range(n):out=mul(out,a)
    return out
def deriv(a):return p([i*c for i,c in enumerate(p(a))][1:])
def ev(a,x):
    out=0
    for c in reversed(p(a)):out=(out*x+c)%P
    return out

def rational_map(a,b,h):
    """Derive N/D from log derivatives of monic h: X=N/h^2, Y=y X'.
    For kernel roots r, sum_r (z-r)^-1=h'/h.
    X=z+2 sum_r[(3r^2+a)/(z-r)] +4 sum_r[f(r)/(z-r)^2].
    """
    h=p(h);f=p((b,a,0,1));d=deriv(h);hh=mul(h,h)
    s1=(-h[2])%P;s2=(h[2]*h[2]-2*h[1])%P
    A=sub(mul(mul(p((a,0,3)),d),h),mul(p((3*s1,9)),hh))
    K=sub(add(mul(mul(deriv(f),d),h),mul(f,sub(mul(deriv(d),h),mul(d,d)))),mul(p((s1,6)),hh))
    N=sub(add(mul(p((0,1)),hh),scale(A,2)),scale(K,4))
    D=hh;W=sub(mul(deriv(N),D),mul(N,deriv(D)))
    return f,N,D,W

def point_add(a,R,S):
    if R is None:return S
    if S is None:return R
    x,y=R;u,v=S
    if x==u and (y+v)%P==0:return None
    if x==u:
        if y==0:return None
        slope=(3*x*x+a)*pow(2*y,-1,P)%P
    else:slope=(v-y)*pow((u-x)%P,-1,P)%P
    x0=(slope*slope-x-u)%P
    return (x0,(slope*(x-x0)-y)%P)

def points(a,b):
    return [None]+[(x,y) for x in range(P) for y in range(P) if (y*y-x*x*x-a*x-b)%P==0]

def make_map(N,D,W,R):
    if R is None:return None
    x,y=R;d=ev(D,x)
    if not d:raise ValueError('kernel intersects rational source group')
    return (ev(N,x)*pow(d,-1,P)%P, y*ev(W,x)*pow(d,-2,P)%P)

def main():
    for name,a,b,h,aa,bb,order in CASES:
        f,N,D,W=rational_map(a,b,h)
        lhs=mul(f,mul(W,W))
        rhs=mul(D,add(add(pw(N,3),scale(mul(N,pw(D,2)),aa)),scale(pw(D,3),bb)))
        assert lhs==rhs, (name,'global rational-function identity failed')
        # Perturbing destination b must break the identity.
        wrong=mul(D,add(add(pw(N,3),scale(mul(N,pw(D,2)),aa)),scale(pw(D,3),bb+1)))
        assert lhs!=wrong, (name,'negative control failed')
        src=points(a,b);dst=points(aa,bb)
        assert len(src)==order==len(dst)
        mapped={R:make_map(N,D,W,R) for R in src}
        assert len(set(mapped.values()))==order
        assert all(Q is None or (Q[1]*Q[1]-Q[0]**3-aa*Q[0]-bb)%P==0 for Q in mapped.values())
        # Every ordered pair, not only generator multiples.
        assert all(mapped[point_add(a,R,S)]==point_add(aa,mapped[R],mapped[S]) for R in src for S in src)
        print(f'{name}: polynomial identity, wrong-target rejection, {order} points, {order**2} homomorphism pairs PASS [pcc:unverified]')

if __name__ == '__main__':main()
