#!/usr/bin/env python3
"""CT47 finite 2-primary Frobenius module compatibility controls. [pcc:unverified]"""
P=101
TRACES=(-7,-11)

def check(test, description):
    if not test:
        raise ArithmeticError(description)

def mul(A,B,m):
    return ((A[0]*B[0]+A[1]*B[2])%m,(A[0]*B[1]+A[1]*B[3])%m,
            (A[2]*B[0]+A[3]*B[2])%m,(A[2]*B[1]+A[3]*B[3])%m)

def mpow(A,n,m):
    out=(1,0,0,1)
    while n:
        if n&1: out=mul(out,A,m)
        A=mul(A,A,m);n>>=1
    return out

def C(trace,m):return (0,-P%m,1,trace%m)
def det(A,m):return (A[0]*A[3]-A[1]*A[2])%m
def conjugate(A,B,X,m):return mul(X,A,m)==mul(B,X,m)
def v2(n):
    check(n!=0,"nonzero required")
    return (abs(n)&-abs(n)).bit_length()-1

def trace_power(t,k):
    if k==0:return 2
    a,b=2,t
    for _ in range(2,k+1):a,b=b,t*b-P*a
    return b

def is_conjugate_exhaustive(k,m):
    A=mpow(C(-7,m),k,m);B=mpow(C(-11,m),k,m)
    for a in range(m):
      for b in range(m):
       for c in range(m):
        for d in range(m):
         X=(a,b,c,d)
         if det(X,m)%2 and conjugate(A,B,X,m):return True
    return False

def cyclic_witness(k,m):
    """Build B_F B_E^-1 with B_t = [e1,C_t^k e1]."""
    A=mpow(C(-7,m),k,m);B=mpow(C(-11,m),k,m)
    a=A[2];b=B[2]
    check(a%2 and b%2,"cyclic-basis hypothesis failed")
    inv=pow(a,-1,m)
    return (1,((B[0]-A[0])*inv)%m,0,b*inv%m)

def anti_adjust(X,s):
    """Centralizer-norm correction, constructive for every 2^s."""
    m=1<<s
    target=(-pow(det(X,m),-1,m))%m
    b=0
    for h in range(1,s):
        q=1<<(h+1)
        if (1-7*b+P*b*b-target)%q:
            b+=1<<h
        check((1-7*b+P*b*b-target)%q==0,"Hensel norm lift")
    C0=C(-7,m)
    Z=((1+b*C0[0])%m,b*C0[1]%m,b*C0[2]%m,(1+b*C0[3])%m)
    Y=mul(X,Z,m)
    check(det(Y,m)==(m-1)%m,"antisymplectic norm correction")
    return Y

def scalar_normalized(t,k,r,lam):
    m=1<<(r+4);A=mpow(C(t,m),k,m);d=1<<(r+2)
    check(all(((A[i]-(lam if i in (0,3) else 0))%m)%d==0 for i in range(4)),
          "not scalar to prescribed order")
    return tuple(((A[i]-(lam if i in (0,3) else 0))%m)//d%4 for i in range(4))

def max_depth(k):
    r=v2(k)
    return r+(3 if k%3==0 else 2)

def run():
    base3=[mpow(C(t,16),3,16) for t in TRACES]
    for B in base3:
        check(B[1]%4==0 and B[2]%4==0 and B[0]%4==3 and B[3]%4==3,
              "base3 scalar error")
    base6=[mpow(C(t,32),6,32) for t in TRACES]
    for B in base6:
        check(B[1]%8==0 and B[2]%8==0 and B[0]%8==1 and B[3]%8==1,
              "base6 scalar error")
    for r in range(9):
        k=3*(1<<r);s=r+3;m=1<<s
        E=mpow(C(-7,m),k,m);F=mpow(C(-11,m),k,m)
        swap=(0,1,1,0)
        check(conjugate(E,F,swap,m),f"swap failure k={k}")
        lam=3 if r==0 else 1
        ne=scalar_normalized(-7,k,r,lam)
        nf=scalar_normalized(-11,k,r,lam)
        check(det(ne,4)!=det(nf,4),f"determinant obstruction missing k={k}")
        if r==0:
            check((det(ne,4),det(nf,4))==(1,3),"unexpected k=3 obstruction")
        else:
            check((det(ne,4),det(nf,4))==(3,1),"unexpected k>=6 obstruction")
    for r in range(10):
        k=1<<r;s=r+2;m=1<<s
        delta=trace_power(-7,k)-trace_power(-11,k)
        check(v2(delta)==s,f"trace difference valuation k={k}")
        U=cyclic_witness(k,m)
        check(det(U,m)%2==1 and conjugate(mpow(C(-7,m),k,m),
                 mpow(C(-11,m),k,m),U,m),f"cyclic witness k={k}")
        V=anti_adjust(U,s)
        check(conjugate(mpow(C(-7,m),k,m),mpow(C(-11,m),k,m),V,m),
              f"anti-isometry witness k={k}")
    cases=[1,2,3,4,5,6,7,8,9,10,12,15]
    count=0
    for k in cases:
        for s in (1,2,3,4):
            m=1<<s
            observed=is_conjugate_exhaustive(k,m)
            predicted=(s<=max_depth(k))
            check(observed==predicted,
                  f"exhaustive disagreement k={k}, s={s}: {observed} vs {predicted}")
            count+=1
    for k,s in ((3,4),(6,5),(12,6)):
        check((trace_power(-7,k)-trace_power(-11,k))%(1<<s)==0,
              "trace negative control did not coincide")
        check(s==max_depth(k)+1,"wrong negative control")
    check(max_depth(3)==3 and max_depth(6)==4 and max_depth(12)==5,
          "unexpected depth")
    try:
        check(is_conjugate_exhaustive(3,16),"invalid extra-depth claim")
    except ArithmeticError:
        pass
    else:
        raise ArithmeticError("negative control failed")
    print("CT47 PASS [pcc:unverified]")
    print("scalar_normalization_checks=18; power_of_two_trace_checks=10; cyclic_witness_and_antiisometry_checks=10")
    print(f"full_exhaustive_matrix_cases={count}; trace_only_false_positives=3")
    print("max_torsion_depth: k=2^r => r+2; k=3*2^r => r+3; odd multipliers do not change depth")
    print("first_extension_for_full_2^s_torsion: 2^(s-2), s>=3")

if __name__=='__main__':
    run()
