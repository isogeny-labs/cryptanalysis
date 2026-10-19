"""Exact Boolean degree-three Macaulay rejection for a fixed first product.

The 13-term two-pair resultant is quadratic in the second source-code bits.
A row-span certificate of the constant polynomial excludes every second code.
"""
from itertools import combinations

class Field:
    def __init__(self, n, reduction):
        self.n=n;self.mask=(1<<n)-1;self.reduction=reduction
    def mul(self,a,b):
        out=0
        while b:
            if b&1:out^=a
            b>>=1;a<<=1
            if a>>self.n:a=(a&self.mask)^self.reduction
        return out
    def square(self,a):return self.mul(a,a)
    def frob(self,a,k):
        for _ in range(k):a=self.square(a)
        return a

def source_basis(field,seed,positions,rotation):
    return [field.frob(field.square(1<<(bit+1)) ^
                       field.mul(seed,1<<(bit+1)),rotation) for bit in positions]

def source_value(code,basis):
    value=0
    for i,b in enumerate(basis):
        if code>>i&1:value^=b
    return value

def monomials(f,degree):
    return [0]+[sum(1<<i for i in positions)
                for d in range(1,degree+1)
                for positions in combinations(range(f),d)]

def coefficients(field,terms,p,qbasis):
    """Return constant, linear, squarefree quadratic field coefficients."""
    f=len(qbasis)
    pp=[1,p]
    for _ in range(3):pp.append(field.mul(pp[-1],p))
    A=[0]*5
    for (i,j),value in terms.items():A[j]^=field.mul(value,pp[i])
    linear=[]
    squared=[field.square(q) for q in qbasis]
    for q,q2 in zip(qbasis,squared):
        q3=field.mul(q,q2);q4=field.square(q2)
        linear.append(field.mul(A[1],q)^field.mul(A[2],q2)^
                      field.mul(A[3],q3)^field.mul(A[4],q4))
    quadratic=[]
    for i,j in combinations(range(f),2):
        b=field.mul(squared[i],qbasis[j])^field.mul(qbasis[i],squared[j])
        quadratic.append(field.mul(A[3],b))
    mons=monomials(f,2)
    assert len(mons)==1+f+f*(f-1)//2
    return mons,[A[0],*linear,*quadratic]

def evaluate_boolean(mons,values,code):
    out=0
    for m,value in zip(mons,values):
        if code&m==m:out^=value
    return out

def evaluate_resultant(field,terms,p,q):
    pp=[1,p];qq=[1,q]
    for _ in range(3):pp.append(field.mul(pp[-1],p));qq.append(field.mul(qq[-1],q))
    return __import__('functools').reduce(int.__xor__,
        (field.mul(c,field.mul(pp[i],qq[j])) for (i,j),c in terms.items()),0)

def equation_rows(n,values):
    rows=[0]*n
    for monomial_index,value in enumerate(values):
        bitset=1<<monomial_index
        while value:
            low=value&-value
            rows[low.bit_length()-1]^=bitset
            value^=low
    return rows

def certificate(n,f,mons2,values,degree=3):
    """Return rank and an explicit XOR certificate for 1 in the row span."""
    assert degree==3
    mons3=monomials(f,3)
    indexes={m:i for i,m in enumerate(mons3)}
    maps=[[indexes[m|1<<j] for m in mons2] for j in range(f)]
    eq=equation_rows(n,values)
    row_specs=[];rows=[]
    for bit,row in enumerate(eq):
        row_specs.append([bit,-1]);rows.append(row)
        positions=[];v=row
        while v:
            low=v&-v;positions.append(low.bit_length()-1);v^=low
        for j in range(f):
            mapped=0
            for i in positions:mapped^=1<<maps[j][i]
            row_specs.append([bit,j]);rows.append(mapped)
    pivots={}
    for row_id,row in enumerate(rows):
        v=row;comb=1<<row_id
        while v:
            pivot=v.bit_length()-1
            if pivot not in pivots:
                pivots[pivot]=(v,comb);break
            prior,prior_comb=pivots[pivot]
            v^=prior;comb^=prior_comb
    v=1;comb=0
    while v:
        pivot=v.bit_length()-1
        if pivot not in pivots:break
        prior,prior_comb=pivots[pivot]
        v^=prior;comb^=prior_comb
    if v:
        return {'rank':len(pivots),'monomials':len(mons3),'equations':len(rows),
                'reject':False,'certificate_rows':None}
    selected=[];replay=0
    while comb:
        low=comb&-comb;idx=low.bit_length()-1
        selected.append(row_specs[idx]);replay^=rows[idx];comb^=low
    assert replay==1
    return {'rank':len(pivots),'monomials':len(mons3),'equations':len(rows),
            'reject':True,'certificate_rows':selected}
