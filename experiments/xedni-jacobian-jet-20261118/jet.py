"""First-order Jacobian jets over Z/p² with four shift directions."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Jet:
    v: int
    d: tuple[int,int,int,int]
    p: int

    def __post_init__(self):
        object.__setattr__(self,'v',self.v%(self.p*self.p))
        object.__setattr__(self,'d',tuple(z%self.p for z in self.d))

    @classmethod
    def const(cls,v,p): return cls(v,(0,0,0,0),p)
    def _coerce(self,other): return other if isinstance(other,Jet) else Jet.const(other,self.p)
    def __add__(self,other):
        other=self._coerce(other)
        return Jet(self.v+other.v,tuple(a+b for a,b in zip(self.d,other.d)),self.p)
    __radd__=__add__
    def __neg__(self): return Jet(-self.v,tuple(-z for z in self.d),self.p)
    def __sub__(self,other): return self+-self._coerce(other)
    def __rsub__(self,other): return self._coerce(other)+-self
    def __mul__(self,other):
        other=self._coerce(other)
        return Jet(self.v*other.v,
                   tuple(self.v*b+other.v*a for a,b in zip(self.d,other.d)),self.p)
    __rmul__=__mul__
    def __pow__(self,n):
        assert n>=0
        out=Jet.const(1,self.p); base=self
        while n:
            if n&1: out=out*base
            base=base*base; n//=2
        return out
    def zero(self): return self.v==0 and all(z==0 for z in self.d)

def jdbl(P,A,p):
    X,Y,Z=P
    if Z.zero() or Y.zero():
        C=lambda v:Jet.const(v,p)
        return C(0),C(1),C(0)
    XX=X*X; YY=Y*Y; YYYY=YY*YY; ZZ=Z*Z
    S=2*((X+YY)**2-XX-YYYY)
    V=3*XX+A*ZZ*ZZ
    X3=V*V-2*S
    Y3=V*(S-X3)-8*YYYY
    Z3=(Y+Z)**2-YY-ZZ
    return X3,Y3,Z3

def jadd(P,Q,A,p):
    if P[2].zero(): return Q
    if Q[2].zero(): return P
    X1,Y1,Z1=P; X2,Y2,Z2=Q
    Z1Z1=Z1*Z1; Z2Z2=Z2*Z2
    U1=X1*Z2Z2; U2=X2*Z1Z1
    S1=Y1*Z2*Z2Z2; S2=Y2*Z1*Z1Z1
    if U1==U2: return jdbl(P,A,p) if S1==S2 else tuple(Jet.const(z,p) for z in (0,1,0))
    H=U2-U1
    I=(2*H)**2; J=H*I; R=2*(S2-S1); V=U1*I
    X3=R*R-J-2*V
    Y3=R*(V-X3)-2*S1*J
    Z3=((Z1+Z2)**2-Z1Z1-Z2Z2)*H
    return X3,Y3,Z3

def jmul(n,P,A,p):
    C=lambda v:Jet.const(v,p)
    out=(C(0),C(1),C(0))
    while n:
        if n&1: out=jadd(out,P,A,p)
        P=jdbl(P,A,p); n//=2
    return out

def leading_jet(q,p,A0,dA,points):
    """Return c(0) and four slopes for each of two centered lift points.

    dA[j] is the coefficient of p*s_j in A modulo p². Point directions
    are x1,y1,x2,y2; all coordinates of points are ordinary integers.
    """
    assert len(dA)==4 and len(points)==2
    C=lambda v:Jet.const(v,p)
    A=Jet(A0,tuple(dA),p)
    out=[]
    for which,(x,y) in enumerate(points):
        dx=[0]*4; dy=[0]*4
        dx[2*which]=1; dy[2*which+1]=1
        P=(Jet(x,tuple(dx),p),Jet(y,tuple(dy),p),C(1))
        X,Y,Z=jmul(q,P,A,p)
        if Z.v%p or X.v%p==0 or Y.v%p==0:
            raise ValueError('jet_q_multiple_not_in_normal_form')
        iy=pow(Y.v%p,-1,p)
        c=(-X.v*(Z.v//p)*iy)%p
        ds=tuple((-X.v*z*iy)%p for z in Z.d)
        out.append((c,ds))
    return out
