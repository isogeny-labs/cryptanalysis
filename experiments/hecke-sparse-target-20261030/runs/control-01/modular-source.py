"""Finite-field q-expansion reconstruction of X0(11) Hecke moments.

No Sage dependency. Every reconstructed function is checked beyond its
leading-pole interpolation conditions, and each admitted fiber is group-checked.
"""
from math import gcd
import numpy as np
from flint import nmod_poly as Poly, nmod_mat as Mat, fmpz_poly


class Laurent:
    def __init__(self, poly, lo, precision):
        self.poly, self.lo, self.precision = poly, lo, precision

    def coeff(self, k):
        assert k < self.precision, (k, self.precision)
        return int(self.poly[k-self.lo]) if k >= self.lo else 0

    def __mul__(self, other):
        bound = min(self.precision+other.lo, other.precision+self.lo)
        lo = self.lo+other.lo
        return Laurent((self.poly*other.poly).truncate(bound-lo), lo, bound)


def q_coordinates(p, precision):
    """Integrate eta(q)^2 eta(q^11)^2, then compose the Weierstrass expansion."""
    one = Poly([1], p)
    eta = one
    for n in range(1, precision):
        for exponent in (n, 11*n):
            if exponent < precision:
                term = [0]*(2*exponent+1)
                term[0], term[exponent], term[2*exponent] = 1, -2, 1
                eta = (eta*Poly(term, p)).truncate(precision)
    z = Poly([0]+[int(eta[n-1])*pow(n, -1, p) % p
                      for n in range(1, precision)], p)
    unit = z.right_shift(1)
    inverse = unit.inverse_series_trunc(precision)
    # For Y²=X³+A X+B: wp(z)=z^-2+sum c_n z^(2n), y=wp'/2.
    A, B = -31*pow(3, -1, p) % p, -2501*pow(108, -1, p) % p
    c = {1: -A*pow(5, -1, p) % p, 2: -B*pow(7, -1, p) % p}
    for n in range(3, precision//2+1):
        c[n] = 6*sum(c[i]*c[n-1-i] for i in range(1, n-1)) * pow((2*n-4)*(2*n+3) % p, -1, p) % p
    x = (inverse*inverse).truncate(precision+2)
    z2, power = (z*z).truncate(precision), one
    for n in range(1, precision//2):
        power = (power*z2).truncate(precision)
        x += (power*c[n]).left_shift(2)
    x += Poly([0, 0, pow(3, -1, p)], p)
    x = x.truncate(precision)
    # q*x'(q)/f(q) = 2y+1.
    derivative = Poly([(i-2)*int(x[i]) for i in range(len(x))], p)
    y = (derivative*eta.inverse_series_trunc(precision)).truncate(precision)
    y = y*pow(2, -1, p) - Poly([0,0,0,pow(2, -1, p)], p)
    return Laurent(x, -2, precision-2), Laurent(y, -3, precision-3), eta


def j_series(p, precision):
    e4 = [0]*precision
    e4[0] = 1
    for d in range(1, precision):
        for n in range(d, precision, d):
            e4[n] += 240*d**3
    delta = Poly([1], p)
    for n in range(1, precision):
        term = Poly([1]+[0]*(n-1)+[-1], p)
        delta = (delta*term.pow_trunc(24, precision)).truncate(precision)
    poly = (Poly(e4, p).pow_trunc(3, precision)*delta.inverse_series_trunc(precision)).truncate(precision)
    return Laurent(poly, -1, precision-1)


class Curve:
    def __init__(self, p):
        self.p = p
        self.ops = 0

    def contains(self, point):
        if point is None:
            return True
        x,y = point
        return (y*y+y-x*x*x+x*x+10*x+20) % self.p == 0

    def neg(self, point):
        return None if point is None else (point[0], (-point[1]-1) % self.p)

    def add(self, left, right):
        self.ops += 1
        if left is None: return right
        if right is None: return left
        if right == self.neg(left): return None
        x,y = left; u,v = right
        slope = ((3*x*x-2*x-10)*pow((2*y+1) % self.p,-1,self.p) if left==right
                 else (v-y)*pow((u-x) % self.p,-1,self.p)) % self.p
        X = (slope*slope+1-x-u) % self.p
        Y = (-slope*X-y+slope*x-1) % self.p
        assert self.contains((X,Y))
        return X,Y

    def mul(self, n, point):
        if n<0: return self.mul(-n,self.neg(point))
        out = None
        while n:
            if n&1: out=self.add(out,point)
            point=self.add(point,point); n >>= 1
        return out

    def total(self, points):
        out=None
        for point in points: out=self.add(out,point)
        return out


class Field:
    """Exact square-root lookup and vectorized character-sum point counts."""
    def __init__(self,p):
        self.p=p
        self.x=np.arange(p,dtype=np.int64)
        squares=self.x*self.x % p
        self.sqrt=np.full(p,-1,dtype=np.int64)
        self.sqrt[squares]=self.x
        self.cube=(self.x*self.x % p)*self.x % p

    def short_order(self,a,b):
        values=(self.cube+a*self.x+b) % self.p
        return self.p+1+int(np.count_nonzero(self.sqrt[values]>=0)*2-self.p-np.count_nonzero(values==0))

    def curve_order(self):
        return self.short_order(-31*pow(3,-1,self.p) % self.p,-2501*pow(108,-1,self.p) % self.p)

    def lifts(self,x):
        x=int(x)%self.p
        disc=(4*(x*x*x-x*x-10*x-20)+1)%self.p
        s=int(self.sqrt[disc])
        if s<0:return []
        inv2=pow(2,-1,self.p)
        return sorted(set((x,((-1+sign*s)*inv2)%self.p) for sign in (1,-1)))

    def j_trace(self,j):
        assert j not in (0,1728 % self.p)
        k=j*pow((1728-j)%self.p,-1,self.p)%self.p
        return self.p+1-self.short_order(3*k%self.p,2*k%self.p)


class Modular:
    def __init__(self,p,degrees):
        self.p,self.degrees=p,list(degrees)
        self.curve=Curve(p)
        precision=240 if max(degrees)<=3 else 420
        self.x,self.y,self.eta=q_coordinates(p,precision)
        maxpole=max(l*(2*l+3) for l in degrees)
        powers=[Laurent(Poly([1],p),0,precision)]
        for _ in range(maxpole//2+2):powers.append(powers[-1]*self.x)
        self.mono={(a,b): powers[a] if b==0 else powers[a]*self.y
                   for b in (0,1) for a in range(len(powers))}
        self.funcs={}
        for l in degrees:
            for kind, ks in [('x',range(1,l+2)),('xy',range(l+1))]:
                for k in ks:
                    source=self.mono[(k,kind=='xy')]
                    pole=l*(2*k+(3 if kind=='xy' else 0))
                    target={n: ((source.coeff(n//l) if n%l==0 else 0)+l*source.coeff(n*l))%p
                            for n in range(-pole,21)}
                    self.funcs[l,kind,k]=self.identify(target,pole)
        jq=j_series(p,precision)
        for x0 in (5,16):
            shifted=Laurent(self.x.poly-Poly([x0],p).left_shift(2),-2,self.x.precision)
            den=Laurent(Poly([1],p),0,precision)
            for _ in range(11):den=den*shifted
            target=den*jq
            try:
                self.jfunc=self.identify({n:target.coeff(n) for n in range(-23,21)},23)
                self.cusp_x=x0
                break
            except AssertionError:pass
        else:raise AssertionError('j-map reconstruction failed')
        self.a={l:int(self.eta[l-1]) for l in degrees}

    def identify(self,target,pole):
        residual=dict(target); result={}
        basis=sorted([(a,b) for (a,b) in self.mono if 2*a+3*b<=pole],key=lambda ab:2*ab[0]+3*ab[1],reverse=True)
        for ab in basis:
            lead=-2*ab[0]-3*ab[1]
            series=self.mono[ab]
            coefficient=residual.get(lead,0)*pow(series.coeff(lead),-1,self.p)%self.p
            if coefficient:
                result[ab]=coefficient
                for n in range(lead,21):residual[n]=(residual.get(n,0)-coefficient*series.coeff(n))%self.p
        assert all(v%self.p==0 for v in residual.values()), 'q-series identity fails surplus coefficients'
        return result

    def evaluate(self,coefficients,point):
        x,y=point
        return sum(c*pow(x,a,self.p)*(y if b else 1) for (a,b),c in coefficients.items())%self.p

    def j(self,point):
        if point is None or point[0]==self.cusp_x:return None
        return self.evaluate(self.jfunc,point)*pow((point[0]-self.cusp_x)%self.p,-11,self.p)%self.p

    def points_with_j(self,j,field):
        a0=Poly([0],self.p);a1=Poly([0],self.p)
        for (a,b),v in self.jfunc.items():
            term=Poly([v],self.p).left_shift(a)
            if b:a1+=term
            else:a0+=term
        X=Poly([0,1],self.p)
        num=j*(X-self.cusp_x)**11-a0
        polynomial=num*num+num*a1-a1*a1*(X**3-X**2-10*X-20)
        out=[]
        for x,_ in polynomial.roots():
            for point in field.lifts(int(x)):
                if self.j(point)==j:out.append(point)
        return out

    def fiber(self,l,point,traces=False):
        p=self.p;d=l+1
        power=[d]+[self.evaluate(self.funcs[l,'x',k],point) for k in range(1,d+1)]
        elementary=[1]
        for k in range(1,d+1):
            elementary.append(sum((-1)**(i-1)*elementary[k-i]*power[i] for i in range(1,k+1))*pow(k,-1,p)%p)
        F=Poly([(-1)**(d-i)*elementary[d-i] for i in range(d+1)],p)
        factors=F.factor()[1]
        pattern=[f.degree() for f,e in factors for _ in range(e)]
        if any(e!=1 for f,e in factors):return dict(status='repeated_x',pattern=pattern)
        # Extend Tr(x^k) by the characteristic-polynomial recurrence.
        for k in range(d+1,2*d-1):power.append(-sum(int(F[j])*power[k-d+j] for j in range(d))%p)
        M=Mat([[power[i+j]%p for j in range(d)] for i in range(d)],p)
        moments=[self.evaluate(self.funcs[l,'xy',k],point) for k in range(d)]
        Y=Poly([int(v[0]) for v in M.solve(Mat([[v] for v in moments],p)).tolist()],p)
        X=Poly([0,1],p)
        assert (Y*Y+Y-X**3+X**2+10*X+20)%F==0
        rational=[];orbit_traces=[]
        for factor,_ in factors:
            if factor.degree()==1:
                x=-int(factor[0])*pow(int(factor[1]),-1,p)%p
                q=x,int(Y(x)); assert self.curve.contains(q)
                rational.append(q);orbit_traces.append(q)
            elif traces:
                orbit_traces.append(extension_trace(X%factor,Y%factor,factor,p))
        complete=len(rational)==d
        if complete:assert self.curve.total(rational)==self.curve.mul(self.a[l],point)
        if traces:assert self.curve.total(orbit_traces)==self.curve.mul(self.a[l],point)
        return dict(status='verified',pattern=pattern,rational=rational,complete=complete,
                    traces=orbit_traces if traces else [], polynomial=[int(c) for c in F.coeffs()])


def extension_trace(x,y,modulus,p):
    """Actual sum of Frobenius conjugates in E(Fp[t]/modulus)."""
    def inverse(a):
        # FLINT xgcd also verifies invertibility in this irreducible quotient.
        g,s,_=a.xgcd(modulus)
        assert g.degree()==0 and int(g[0])!=0
        return (s*pow(int(g[0]),-1,p))%modulus
    def add(left,right):
        if left is None:return right
        if right is None:return left
        x,y=left;u,v=right
        if x==u and (y+v+1)%modulus==0:return None
        slope=((3*x*x-2*x-10)*inverse((2*y+1)%modulus) if left==right
               else (v-y)*inverse((u-x)%modulus))%modulus
        X=(slope*slope+1-x-u)%modulus
        Y=(-slope*X-y+slope*x-1)%modulus
        assert (Y*Y+Y-X**3+X**2+10*X+20)%modulus==0
        return X,Y
    point=(x,y);out=None
    for _ in range(modulus.degree()):
        out=add(out,point)
        point=(point[0].pow_mod(p,modulus),point[1].pow_mod(p,modulus))
    assert point==(x,y)
    if out is None:return None
    assert all(v.degree()<=0 for v in out)
    return int(out[0][0]),int(out[1][0])


def cm_points(modular,field,f,trace_magnitude):
    points=[];strata=[]
    for conductor in range(1,f+1):
        if f%conductor:continue
        H=fmpz_poly.hilbert_class_poly(-39*conductor*conductor)
        roots=Poly([int(v)%field.p for v in H.coeffs()],field.p).roots()
        assert sum(m for _,m in roots)==H.degree()
        local=[]
        for j,multiplicity in roots:
            j=int(j);assert multiplicity==1
            assert abs(field.j_trace(j))==trace_magnitude
            local.extend(modular.points_with_j(j,field))
        assert len(local)==2*H.degree()
        strata.append(dict(conductor=conductor,class_number=H.degree(),points=len(local)))
        points.extend(local)
    assert len(points)==len(set(points))
    return sorted(points),strata
