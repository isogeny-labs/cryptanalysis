#!/usr/bin/env python3
"""CT31: independent F_101^3 x-only 2-torsion gluing replay.
No producer arithmetic, SymPy, or external dependencies. [pcc:unverified].
"""
P=101
MOD=(56,13,6) # T^3+6T^2+13T+56 irreducible

def F(a):
    if isinstance(a, int):return (a%P,0,0)
    if len(a)!=3:raise ValueError(a)
    return tuple(int(v)%P for v in a)

def add(a,b):return tuple((u+v)%P for u,v in zip(F(a),F(b)))
def neg(a):return tuple(-u%P for u in F(a))
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    a,b=F(a),F(b); w=[0]*5
    for i,x in enumerate(a):
        for j,y in enumerate(b):w[i+j]=(w[i+j]+x*y)%P
    for j in (4,3):
        z=w[j]
        for i,c in enumerate(MOD):w[j-3+i]=(w[j-3+i]-z*c)%P
    return tuple(w[:3])
def power(a,k):
    assert k>=0
    out=F(1);a=F(a)
    while k:
        if k&1:out=mul(out,a)
        a=mul(a,a);k//=2
    return out

def div(a,b):
    b=F(b)
    if b==F(0):raise ZeroDivisionError
    return mul(a,power(b,P**3-2))

def polyeval(poly,x):
    y=F(0)
    for c in reversed(poly):y=add(mul(y,x),F(c))
    return y

def image_2torsion(t,a,h):
    """Vélu on y=0: x' = 7t + 2 h_2 - 2 f'(t)h'(t)/h(t).
    From summing x(P+Q)+x(P-Q)-2x(Q) over 3 kernel x-pairs.
    """
    t=F(t)
    H=polyeval(h,t)
    if H==F(0):raise ValueError('non-coprime 2/7 kernel')
    der_f=add(mul(F(3),mul(t,t)),F(a))
    der_h=polyeval((h[1],2*h[2],3),t)
    return sub(add(mul(F(7),t),F(2*h[2])),mul(F(2),div(mul(der_f,der_h),H)))

def cubic_short(b,c,d):
    # u^3+d*u^2+c*u+b, with U=u+d/3
    shift=(d*pow(3,-1,P))%P
    a=(c-d*d*pow(3,-1,P))%P
    B=(b-c*shift+2*pow(d,3,P)*pow(27,-1,P))%P
    return shift,a,B

def chart(b,c,d,targets):
    cubics=((b,c,d),(b*b%P,d*b%P,c))
    ret=[]
    for b0,c0,d0 in cubics:
        shift,a,B=cubic_short(b0,c0,d0)
        found=[(i,k) for i,(ta,tb) in enumerate(targets) for k in range(1,P)
               if a*pow(k,4,P)%P==ta and B*pow(k,6,P)%P==tb]
        assert found,('no quotient chart',b,c,d,b0,c0,d0,a,B)
        # k and -k have identical x action; choose smallest.
        i,k=min(found)
        ret.append((i,shift,pow(k,2,P)))
    assert {x[0] for x in ret}=={0,1},ret
    return ret

def get_internal(x,chart):
    _,shift,k2=chart
    return sub(div(x,F(k2)),F(shift))

def transport(original,edges):
    t=original
    for a,h in edges:t=image_2torsion(t,a,h)
    return t

def check(ok,message):
    if not ok:raise AssertionError(message)

def main():
    check(all(polyeval((56,13,6,1),F(j))!=F(0) for j in range(P)),
          "cubic modulus must be irreducible")
    t=F((0,1,0)); z=[t,power(t,P),power(t,P*P)]
    check(power(z[2],P)==z[0],'Frobenius closure g')
    check(all(polyeval((56,13,6,1),r)==F(0) for r in z),'cubic roots')
    E0=[(1,46),(44,21)]
    E1=[(26,58),(69,50)]
    E2=[(59,27),(23,7)]
    alpha=[(72,100,35,1),(59,46,8,1)]
    beta=[(99,94,75,1),(53,19,40,1)]
    # Fixed original HLP matching from the actual sextic C0.
    origin=[[add(r,F(2)) for r in z],
            [add(div(F(56),r),F(38)) for r in z]]
    out1=[[transport(r,[(E0[i][0],alpha[i])]) for r in origin[i]] for i in range(2)]
    out2=[[transport(r,[(E0[i][0],alpha[i]),(E1[i][0],beta[i])])
           for r in origin[i]] for i in range(2)]
    charts1=chart(68,42,26,E1)
    charts2=chart(19,10,22,E2)
    for stage,(out,targets,chs,b) in enumerate(((out1,E1,charts1,68),(out2,E2,charts2,19)),1):
        for i in range(2):
            check(len(set(out[i]))==3,f'collapsed E2[{i}] torsion')
            for j,x in enumerate(out[i]):
                check(add(add(mul(mul(x,x),x),mul(F(targets[i][0]),x)),F(targets[i][1]))==F(0),
                    f'wrong target 2-torsion stage {stage}/{i}/{j}')
                check(power(x,P)==out[i][(j+1)%3],f'broken Frobenius {stage}/{i}/{j}')
        for j in range(3):
            v=[get_internal(out[ch[0]][j],ch) for ch in chs]
            check(mul(v[0],v[1])==F(b),f'wrong actual gluing support stage{stage} root{j}')
        print(f'stage{stage}: charts={chs}, 3 geometric 2-torsion matches, cubic identities, Galois orbit PASS [pcc:unverified]')
    # Negative control: shift the second target triple by 1 Frobenius step;
    # each individual target remains a valid E[2] Frobenius orbit, but
    # the matched graph is changed (not an actual transported HLP graph).
    bad=[out2[0],out2[1][1:]+out2[1][:1]]
    failures=0
    for j in range(3):
        v=[get_internal(bad[ch[0]][j],ch) for ch in charts2]
        if mul(v[0],v[1])!=F(19):failures+=1
    check(failures==3,f'rotated gluing negative control {failures}/3')
    print('rotated Galois-equivariant wrong matching rejected 3/3; no genus-2 arithmetic or speed claim [pcc:unverified]')

if __name__=='__main__':main()
