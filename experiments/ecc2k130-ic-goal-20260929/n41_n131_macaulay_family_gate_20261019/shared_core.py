"""Reuse the fixed cubic Macaulay projection of the normalized resultant."""
from itertools import combinations
from macaulay import monomials,coefficients,equation_rows

def inverse(field,a):
    assert a
    exponent=(1<<field.n)-2
    out=1
    while exponent:
        if exponent&1:out=field.mul(out,a)
        a=field.square(a);exponent>>=1
    return out

def normalize(field,terms,p,qbasis):
    mons,values=coefficients(field,terms,p,qbasis)
    c13=terms[(1,3)];c33=terms[(3,3)]
    p3=field.mul(p,field.square(p))
    leading=field.mul(c13,p)^field.mul(c33,p3)
    assert leading
    inv=inverse(field,leading)
    assert field.mul(leading,inv)==1
    return mons,[field.mul(value,inv) for value in values],leading

class SharedCubicCore:
    def __init__(self,n,f,mons2,normalized_values):
        self.n=n;self.f=f;self.mons2=mons2
        self.mons3=monomials(f,3)
        self.low=[m for m in self.mons3 if m.bit_count()<=2]
        self.high=[m for m in self.mons3 if m.bit_count()==3]
        assert self.low==mons2
        self.low_index={m:i for i,m in enumerate(self.low)}
        self.high_index={m:i for i,m in enumerate(self.high)}
        self.quadratic=normalized_values[1+f:]
        assert len(self.quadratic)==f*(f-1)//2
        self.high_rows=[0]*(n*f)
        for (i,k),coeff in zip(combinations(range(f),2),self.quadratic):
            bits=[];v=coeff
            while v:
                bit=v&-v;bits.append(bit.bit_length()-1);v^=bit
            for j in range(f):
                if j==i or j==k:continue
                column=1<<self.high_index[(1<<i)|(1<<k)|(1<<j)]
                for bit in bits:self.high_rows[bit*f+j]^=column
        pivots={};self.nullcombs=[]
        for row_id,row in enumerate(self.high_rows):
            v=row;comb=1<<row_id
            while v:
                pivot=v.bit_length()-1
                if pivot not in pivots:
                    pivots[pivot]=(v,comb);break
                old,oldcomb=pivots[pivot];v^=old;comb^=oldcomb
            if not v:self.nullcombs.append(comb)
        self.high_rank=len(pivots)
        assert self.high_rank+len(self.nullcombs)==n*f
        self.low_maps=[[self.low_index.get(m|1<<j,-1) for m in mons2]
                       for j in range(f)]
    def check(self,normalized_values):
        assert normalized_values[1+self.f:]==self.quadratic
        equations=equation_rows(self.n,normalized_values)
        multiplied=[]
        for bit,row in enumerate(equations):
            positions=[];v=row
            while v:
                low=v&-v;positions.append(low.bit_length()-1);v^=low
            for j in range(self.f):
                mapped=0;mapping=self.low_maps[j]
                for index in positions:
                    column=mapping[index]
                    if column>=0:mapped^=1<<column
                multiplied.append(mapped)
        assert len(multiplied)==self.n*self.f
        low_rows=list(equations)
        for comb in self.nullcombs:
            v=0
            while comb:
                low=comb&-comb;v^=multiplied[low.bit_length()-1];comb^=low
            low_rows.append(v)
        pivots={}
        for row in low_rows:
            v=row
            while v:
                pivot=v.bit_length()-1
                if pivot not in pivots:pivots[pivot]=v;break
                v^=pivots[pivot]
        v=1
        while v:
            pivot=v.bit_length()-1
            if pivot not in pivots:break
            v^=pivots[pivot]
        return {'high_rank':self.high_rank,'low_rank':len(pivots),
                'rank':self.high_rank+len(pivots),'reject':v==0,
                'high_nullity':len(self.nullcombs),'low_rows':len(low_rows)}
