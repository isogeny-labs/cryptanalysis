#!/usr/bin/env python3
"""Independently enumerate F101-rational Frobenius-stable genus-2 Richelot matchings.
For the even-sextic 3+3 family, work in F101[t]/(first irreducible cubic).
"""
P=101
DATA={
    "Cpi1": ((3,26,3,1), (52,0,25,0,77,0,84)),
    "Cpi2": ((3,-3,18,1), (72,0,85,0,14,0,93)),
    "C10": ((-38,-16,7,1), (89,0,93,0,8,0,61)),
    "C20": ((3,46,24,1), (40,0,45,0,75,0,18)),
}
def ck(ok,msg):
    if not ok: raise ValueError(msg)
class Cubic:
    def __init__(self,c):
        self.f=tuple(x%P for x in c[:3]);ck(len(c)==4 and c[3]==1,"nonmonic")
        self.z=(0,0,0);self.one=(1,0,0);self.alpha=(0,1,0)
    def c(self,n):return(n%P,0,0)
    def add(self,a,b):return tuple((x+y)%P for x,y in zip(a,b))
    def neg(self,a):return tuple(-x%P for x in a)
    def sub(self,a,b):return self.add(a,self.neg(b))
    def mul(self,a,b):
        v=[0]*5
        for i in range(3):
            for j in range(3):v[i+j]=(v[i+j]+a[i]*b[j])%P
        for i in (4,3):
            t=v[i]
            for j in range(3):v[i-3+j]=(v[i-3+j]-t*self.f[j])%P
        return tuple(v[:3])
    def pow(self,a,n):
        z=self.one
        while n:
            if n&1:z=self.mul(z,a)
            a=self.mul(a,a)
            n>>=1
        return z
    def det(self,rows):
        a,b,c=rows
        triple=lambda x,y,z:self.mul(self.mul(x,y),z)
        pos=self.add(self.add(triple(a[0],b[1],c[2]),triple(a[1],b[2],c[0])),triple(a[2],b[0],c[1]))
        neg=self.add(self.add(triple(a[2],b[1],c[0]),triple(a[1],b[0],c[2])),triple(a[0],b[2],c[1]))
        return self.sub(pos,neg)
def countmatch(permutation):
    def full_matchings(remaining):
        if not remaining:yield ()
        else:
            i=min(remaining)
            for j in remaining:
                if j!=i:
                    for tail in full_matchings(remaining-{i,j}):yield tuple(sorted(((i,j),)+tail))
    allmatch=set(full_matchings(set(range(6))))
    stable={m for m in allmatch if tuple(sorted(tuple(sorted((permutation[i],permutation[j]))) for i,j in m))==m}
    return allmatch,stable
def target_coeffs(name,shift):
    g,f=DATA[name];F=Cubic(g)
    r=[F.alpha,F.pow(F.alpha,P),F.pow(F.alpha,P*P)]
    q=[]
    for i in range(3):
        a,b=r[i],F.neg(r[(i+shift)%3])
        q.append([F.mul(a,b),F.neg(F.add(a,b)),F.one])
    delta=F.det(q)
    ck(delta!=F.z,'degenerate')
    def pad(a,n):return a+[F.z]*(n-len(a))
    def poly_mul(a,b):
        c=[F.z]*(len(a)+len(b)-1)
        for i,x in enumerate(a):
            for j,y in enumerate(b):c[i+j]=F.add(c[i+j],F.mul(x,y))
        return c
    def diff(a):return [F.mul(F.c(i),a[i]) for i in range(1,len(a))]
    def minus(a,b):return [F.sub(x,y) for x,y in zip(pad(a,max(len(a),len(b))),pad(b,max(len(a),len(b))))]
    def bracket(a,b):return minus(poly_mul(diff(a),b),poly_mul(a,diff(b)))
    def norm(a):
        while a and a[-1]==F.z:a.pop()
        return a
    h=[norm(bracket(q[(i+1)%3],q[(i+2)%3])) for i in range(3)]
    prod=poly_mul(poly_mul(h[0],h[1]),h[2])
    inverse=F.pow(F.mul(F.c(f[6]),F.pow(delta,3)),P**3-2)
    cod=[F.mul(c,inverse) for c in prod]
    ck(all(y[1:]==(0,0) for y in cod),"does not descend")
    coeff=[x[0] for x in cod]
    ck(len(coeff)==7,'unexpected target degree')
    print('codomain',name,shift,coeff)
    return coeff
def main():
    six=list(range(1,6))+[0]
    all_six,stable_six=countmatch(six)
    ck(len(all_six)==15 and len(stable_six)==1,"six-cycle matching count")
    print("T0/T1/T2 six-cycle stable matchings:",len(stable_six),stable_six)
    sigma=[1,2,0,4,5,3]
    all_m,stable=countmatch(sigma)
    ck(len(all_m)==15 and len(stable)==3,"3+3 matching count")
    print("3+3 stable matchings:",len(stable),sorted(stable))
    determinants={'Cpi1':(0,50,51),'Cpi2':(0,81,20),'C10':(0,73,28),'C20':(0,34,67)}
    expected={
      'Cpi1':[[46,8,49,99,4,78,54],[46,93,49,2,4,23,54]],
      'Cpi2':[[77,81,100,16,0,40,71],[77,20,100,85,0,61,71]],
      'C10':[[49,17,85,87,33,9,10],[49,84,85,14,33,92,10]],
      'C20':[[25,98,69,38,52,39,76],[25,3,69,63,52,62,76]],
    }
    for name,(c,f) in DATA.items():
        F=Cubic(c)
        roots=[F.alpha,F.pow(F.alpha,P),F.pow(F.alpha,P*P)]
        ck(F.pow(F.alpha,P**3)==F.alpha,name+' extension')
        ck(len(set(roots))==3,name+' roots collapsed')
        negs=[F.neg(r) for r in roots]
        for j in range(3):
            qrows=[]
            for i in range(3):
                a,b=roots[i],negs[(i+j)%3]
                qrows.append((F.mul(a,b),F.neg(F.add(a,b)),F.one))
            for i in range(3):
                ck(tuple(F.pow(x,P) for x in qrows[i])==qrows[(i+1)%3],name+' Frobenius covariance')
            determinant=F.det(qrows)
            ck(determinant[1:]==(0,0),name+' det does not descend')
            ck(determinant[0]==determinants[name][j],name+' det mismatch')
        for shift in (1,2):
            got=target_coeffs(name,shift)
            ck(got==expected[name][shift-1],name+' target polynomial mismatched')
            ck(all(((-1)**i*expected[name][0][i])%P==expected[name][1][i] for i in range(7)),name+' mirrored control failed')
    print('PASS independent Python: 8 exact targets, all F101-stable matchings')
if __name__=='__main__':main()
