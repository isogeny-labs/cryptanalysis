"""Proposed fixed-norm quadratic lift, with independent extension arithmetic.

Labels belong to T=Tr(R), not to the extension point R itself. This is
a construction check, not an efficient relation solver or an ECDLP attack.
"""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import Curve,prime_order_curve,sqrt_mod


class Extension:
    def __init__(self,p,delta):self.p,self.delta=p,delta
    def add(self,x,y):return ((x[0]+y[0])%self.p,(x[1]+y[1])%self.p)
    def neg(self,x):return (-x[0]%self.p,-x[1]%self.p)
    def sub(self,x,y):return self.add(x,self.neg(y))
    def mul(self,x,y):
        a,b=x;c,d=y;p=self.p
        return ((a*c+self.delta*b*d)%p,(a*d+b*c)%p)
    def inv(self,x):
        a,b=x;p=self.p;n=pow((a*a-self.delta*b*b)%p,-1,p)
        return (a*n%p,-b*n%p)
    def div(self,x,y):return self.mul(x,self.inv(y))
    def conjugate(self,x):return (x[0],-x[1]%self.p)
    def point_add(self,E,P,Q):
        if P is None:return Q
        if Q is None:return P
        x,y=P;xx,yy=Q
        if x==xx:
            if self.add(y,yy)==(0,0):return None
            slope=self.div(self.add(self.mul((3,0),self.mul(x,x)),(E.a,0)),self.mul((2,0),y))
        else:slope=self.div(self.sub(yy,y),self.sub(xx,x))
        rx=self.sub(self.sub(self.mul(slope,slope),x),xx)
        return rx,self.sub(self.mul(slope,self.sub(x,rx)),y)
    def contains(self,E,R):
        if R is None:return True
        x,y=R
        rhs=self.add(self.add(self.mul(self.mul(x,x),x),self.mul((E.a,0),x)),(E.b,0))
        return self.mul(y,y)==rhs


def lift(E,T,nu,delta,nonrational=True):
    """All quadratic-extension lifts of T with norm(x)=nu, in degree <=4."""
    p=E.p;X,Y=T
    if X==0:slopes=[(nu-E.a)*pow(2*Y,-1,p)%p]
    else:
        h=sqrt_mod(E.b+X*nu,p)
        if h is None:return []
        slopes={(-Y+h)*pow(X,-1,p)%p,(-Y-h)*pow(X,-1,p)%p}
    result=set()
    for s in slopes:
        a=(s*s-X)*pow(2,-1,p)%p
        beta=sqrt_mod((a*a-nu)*pow(delta,-1,p),p)
        if beta is None or (nonrational and beta==0):continue
        c=(s*(a-X)-Y)%p
        for d in {beta,-beta%p}:result.add(((a,d),(c,s*d%p)))
    return sorted(result)


def main():
    records=[];tests=verified=0
    for p in [17,41,97,1153]:
        E,r,P=prime_order_curve(p)
        delta=next(d for d in range(2,p) if sqrt_mod(d,p) is None)
        K=Extension(p,delta);targets=list(E.points())
        nus=range(1,p) if p<=97 else [1,2,3,5,7]
        for nu in nus:
            success=points=0
            for T in targets:
                candidates=lift(E,T,nu,delta)
                tests+=1;success+=bool(candidates)
                assert len(candidates)<=4
                for R in candidates:
                    assert K.contains(E,R)
                    xx,yy=R
                    assert K.mul(xx,K.conjugate(xx))==(nu%p,0)
                    conjugate=(K.conjugate(xx),K.conjugate(yy))
                    assert K.point_add(E,R,conjugate)==((T[0],0),(T[1],0))
                    points+=1;verified+=1
            records.append({'p':p,'curve':[E.a,E.b],'order':r,'nu':nu,'delta':delta,
                            'targets':len(targets),'liftable_targets':success,
                            'nonrational_lifts_verified':points})
        print({'p':p,'constants_tested':len(nus),'targets_per_constant':len(targets)},flush=True)
    output={'target_constant_pairs':tests,'extension_lifts_verified':verified,
            'labels_are_on_trace_only':True,'relation_solver_not_demonstrated':True,
            'errors':0,'records':records}
    Path(__file__).with_name('norm_trace_validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print({key:value for key,value in output.items() if key!='records'},flush=True)


if __name__=='__main__':main()
