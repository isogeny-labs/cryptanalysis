"""Groebner solving degree: degree-N membership vs boolean indicators."""
import sys, time
from sympy import symbols, groebner, expand, prod, Poly

p, a, b = 1009, 3, 7

def pts_with_x(x):
    rhs = (x*x*x + a*x + b) % p
    return [y for y in range(p) if (y*y) % p == rhs]

def add(P, Q):
    if P is None: return Q
    if Q is None: return P
    (x1,y1),(x2,y2) = P,Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if x1 == x2 and y1 == y2:
        lam = (3*x1*x1 + a) * pow(2*y1, -1, p) % p
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (lam*lam - x1 - x2) % p
    return (x3, (lam*(x1 - x3) - y1) % p)

B = []
for x in range(p):
    ys = pts_with_x(x)
    if ys: B.append(x)
    if len(B) == 4: break
P1 = (B[0], pts_with_x(B[0])[0]); P2 = (B[1], pts_with_x(B[1])[0])
R = add(P1, P2); xR = R[0]
print("B =", B, "xR =", xR, flush=True)

def s3(x1, x2):
    return expand((x1-x2)**2*xR**2 - 2*((x1+x2)*(x1*x2+a)+2*b)*xR + (x1*x2-a)**2 - 4*b*(x1+x2))

def run(mode):
    t0=time.time()
    if mode=="poly":
        x1,x2 = symbols("x1 x2")
        gens=[s3(x1,x2), expand(prod([x1-v for v in B])), expand(prod([x2-v for v in B]))]
        vs=[x1,x2]
    else:
        z1=symbols("u0:%d" % len(B)); z2=symbols("v0:%d" % len(B)); x1,x2=symbols("x1 x2")
        gens=[z**2-z for z in list(z1)+list(z2)]
        gens+=[sum(z1)-1, sum(z2)-1, x1-sum(v*z for v,z in zip(B,z1)), x2-sum(v*z for v,z in zip(B,z2)), s3(x1,x2)]
        vs=list(z1)+list(z2)+[x1,x2]
    G=groebner(gens,*vs,modulus=p,order="grevlex")
    degs=[Poly(g,*vs,modulus=p).total_degree() for g in G.polys]
    return dict(mode=mode,N=len(B),vars=len(vs),basis=len(G.polys),maxdeg=max(degs) if degs else 0,secs=round(time.time()-t0,2))

for m in ("poly","bool"):
    try: print(run(m), flush=True)
    except Exception as e: print({"mode":m,"err":str(e)[:100]}, flush=True)
