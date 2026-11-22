from research import *
import signal

def main():
 rec=json.loads((OUT/'results.json').read_text())['symbolic'][0]
 p,A=rec['p'],rec['A'];C=Curve(p,A,1);B=list(map(tuple,rec['base']));R=tuple(rec['target'])
 d=-(A-2)*pow(A+2,-1,p)%p;c=next(i for i in range(p) if i*i%p==(-A-2)%p)
 def ed(P):
  if P is None:return (0,1)
  u,v=P;return c*u*pow(v,-1,p)%p,(u-1)*pow(u+1,-1,p)%p
 xr,yr=ed(R);h,t,w,t1,t2,x1,x2,y1,y2=S.symbols('h t w t1 t2 x1 x2 y1 y2');vs=[h,t,w,t1,t2,x1,x2,y1,y2]
 ys=[ed(P)[1] for P in B]
 eq=[t1-x1*y1,t2-x2*y2,-x1*x1+y1*y1-1-d*t1*t1,-x2*x2+y2*y2-1-d*t2*t2,t-x1*x2,w-y1*y2,h-t*w,xr*(1+d*h)-x1*y2-y1*x2,yr*(1-d*h)-w-t,S.prod(y1-y for y in ys),S.prod(y2-y for y in ys)]
 base={'p':p,'A':A,'base':B,'target':R,'variables':list(map(str,vs)),'equations':list(map(str,eq)),'constraint_count':len(eq),'max_input_degree':max(S.Poly(e,*vs).total_degree() for e in eq),'limit_seconds':45,'scope':'full retained-system reference correctness; not a solver benchmark'}
 def timeout(sig,frame):raise TimeoutError('fixed correctness-test limit')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(45)
 try:
  G=S.groebner(eq,*vs,modulus=p,order='grevlex',method='f5b')
  signal.alarm(0);n=0;solutions=0
  for P in signset(C,B):
   for Q in signset(C,B):
    a,b=ed(P);c_,d_=ed(Q)
    vals={x1:a,y1:b,x2:c_,y2:d_,t1:a*b%p,t2:c_*d_%p,t:a*c_%p,w:b*d_%p,h:a*b*c_*d_%p}
    accepted=all(int(e.subs(vals))%p==0 for e in eq)
    reduced=all(int(e.as_expr().subs(vals))%p==0 for e in G.polys)
    assert accepted==reduced==(C.add(P,Q)==R)
    n+=1;solutions+=accepted
  base.update(status='passed',checked_signed_pairs=n,verified_solutions=solutions,basis_polynomials=len(G.polys),output_terms=sum(len(f.terms()) for f in G.polys),output_max_degree=max(int(f.total_degree()) for f in G.polys))
 except TimeoutError:base.update(status='timeout',conclusion='no correctness outcome from this reference solve; no comparative cost inference')
 (OUT/'retained-results.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps(base))
if __name__=='__main__':main()
