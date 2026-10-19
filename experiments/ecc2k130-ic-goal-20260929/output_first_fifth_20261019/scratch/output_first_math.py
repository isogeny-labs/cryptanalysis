"""Exact GF(2^n) and binary-curve primitives for output-first fixed-seed inversion."""
class Field:
    def __init__(self,n,taps):
        self.n=n;self.mod=(1<<n)|sum(1<<i for i in taps)
    def reduce(self,a):
        while a.bit_length()>self.n:a^=self.mod<<(a.bit_length()-self.n-1)
        return a
    def mul(self,a,b):
        out=0
        while b:
            if b&1:out^=a
            b>>=1;a<<=1
            if a>>self.n:a^=self.mod
        return out
    def square(self,a):
        out=0
        while a:
            bit=a&-a;out^=1<<(2*(bit.bit_length()-1));a^=bit
        return self.reduce(out)
    def inverse(self,a):
        assert a
        u,v,g,h=a,self.mod,1,0
        while u!=1:
            assert u
            j=u.bit_length()-v.bit_length()
            if j<0:u,v=v,u;g,h=h,g;j=-j
            u^=v<<j;g^=h<<j
        return self.reduce(g)
    def frob(self,a,k):
        for _ in range(k):a=self.square(a)
        return a
    def trace(self,a):
        total=0
        for _ in range(self.n):total^=a;a=self.square(a)
        assert total in (0,1)
        return total
    def halftrace_exact(self,a):
        assert self.trace(a)==0
        original=a;total=0
        for _ in range((self.n+1)//2):
            total^=a;a=self.square(self.square(a))
        assert self.square(total)^total==original
        return total
class Curve:
    def __init__(self,field):self.f=field
    def on_curve(self,p):
        if p is None:return True
        f=self.f;x,y=p
        return f.square(y)^f.mul(x,y)==f.mul(f.square(x),x)^1
    def neg(self,p):return None if p is None else (p[0],p[0]^p[1])
    def add(self,p,q):
        if p is None:return q
        if q is None:return p
        f=self.f;x,y=p;u,v=q
        if x==u:
            if y!=v:
                assert y^v==x
                return None
            if x==0:return None
            slope=x^f.mul(y,f.inverse(x))
            X=f.square(slope)^slope
            Y=f.square(x)^f.mul(slope^1,X)
        else:
            slope=f.mul(y^v,f.inverse(x^u))
            X=f.square(slope)^slope^x^u
            Y=f.mul(slope,x^X)^X^y
        out=(X,Y)
        assert self.on_curve(out)
        return out
    def sub(self,p,q):return self.add(p,self.neg(q))
    def frob(self,p,k):
        if p is None:return None
        return (self.f.frob(p[0],k),self.f.frob(p[1],k))
class FixedSeed:
    def __init__(self,n,taps,seed_mask,width):
        self.f=Field(n,taps);self.e=Curve(self.f);self.n=n
        self.seed=seed_mask<<1;self.width=width
        self.bits=[i for i in range(width) if i!=seed_mask.bit_length()-1]
        assert len(self.bits)==width-1
        h=self.f.halftrace_exact(self.seed)
        self.H=self.f.square(h);self.C=1^self.H
        assert self.H and self.C
        self.base=[1<<(i+1) for i in self.bits]
        self.product_basis=[self.f.square(a)^self.f.mul(self.seed,a) for a in self.base]
        self.basis={}
        for i,value in enumerate(self.product_basis):
            code=1<<i
            while value:
                pivot=value.bit_length()-1
                if pivot not in self.basis:self.basis[pivot]=(value,code);break
                v,c=self.basis[pivot];value^=v;code^=c
            else:raise AssertionError('dependent product basis')
        assert len(self.basis)==width-1
    def source_a(self,code):
        out=0
        for i,b in enumerate(self.base):
            if code>>i&1:out^=b
        return out
    def source_product(self,code):
        a=self.source_a(code)
        return self.f.mul(a,a^self.seed)
    def code_of_product(self,product):
        code=0;value=product
        while value:
            pivot=value.bit_length()-1
            if pivot not in self.basis:return None
            v,c=self.basis[pivot];value^=v;code^=c
        return code
    def source_valid(self,a):
        if not a or a==self.seed:return False
        f=self.f
        return f.trace(a)==0 and f.trace(f.inverse(a))==0 and f.trace(f.inverse(a^self.seed))==0
    def source_points(self,a):
        f=self.f;e=self.e
        h=f.halftrace_exact(a);assert h
        x=1^f.inverse(h);assert x
        rhs=x^f.inverse(f.square(x))
        t=f.halftrace_exact(rhs)
        y=f.mul(x,t)
        first=(x,y);second=e.neg(first)
        assert e.on_curve(first) and e.on_curve(second)
        return first,second
    def pair_points(self,code,rotation):
        a=self.source_a(code);assert self.source_valid(a)
        left=self.source_points(a);right=self.source_points(a^self.seed)
        points=[self.e.frob(self.e.add(p,q),rotation) for p in left for q in right]
        assert all(p is not None and p[0] for p in points)
        assert len(set(points))==4
        return points
    def column(self,a):
        f=self.f;h=f.halftrace_exact(a);x=1^f.inverse(h)
        return min(f.frob(x,k) for k in range(self.n))
    def recover(self,residual,rotation):
        if residual is None:return {'status':'IDENTITY_RESIDUAL'}
        assert self.e.on_curve(residual)
        x=residual[0]
        if x==0:return {'status':'ZERO_X_RESIDUAL'}
        f=self.f
        base_x=f.frob(x,(self.n-rotation)%self.n)
        p=f.mul(self.H,base_x)^f.mul(self.C,f.inverse(base_x))
        code=self.code_of_product(p)
        if code is None:return {'status':'OUTSIDE_PRODUCT_SUBSPACE'}
        a=self.source_a(code)
        assert self.source_product(code)==p
        if not self.source_valid(a):return {'status':'INELIGIBLE_CODE','code':code,'product':p}
        points=self.pair_points(code,rotation)
        if residual not in points:return {'status':'GROUP_MISMATCH','code':code,'product':p}
        ca,cb=self.column(a),self.column(a^self.seed)
        return {'status':'VERIFIED_PAIR_OUTPUT','code':code,'product':p,
                'source_masks':[a,a^self.seed],'columns':[ca,cb],
                'output_point':list(residual)}
