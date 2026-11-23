"""Verify the archived public M31 relation equations on a degree-seven image curve."""
import json
import subprocess

from archived_loops import observations, read


def main():
    fixture = json.loads(read("public", "json"))
    rows = []
    for arm in ("v2_chain", "v2_batch"):
        for seed in range(3):
            _, records = observations(arm, seed)
            rows.extend([[r[k] for k in ("a", "b", "i", "j", "si", "sj")] for r in records])
    public = fixture["public"]
    assert (public["p"], public["a"], public["b"]) == (2147483647, 2, 14)
    inputs = (f"B={fixture['factor_base']};P={public['P']};Q={public['Q']};R={rows};\n")
    # The three x-coordinates of a cyclic order-seven kernel are closed under doubling.
    script = inputs + """
p=2^31-1; E=ellinit([2,14],p);
h=Mod(1,p)*(x^3+381850961*x^2+786974760*x+1336396478);
X=Mod(x,h); rhs=X^3+2*X+14;
if(elldivpol(E,7)%h!=0 || subst(h,x,(3*X^2+2)^2/(4*rhs)-2*X)!=0,error("kernel"));
z=ellisogeny(E,h); F=ellinit(z[1],p);
phi(P)=ellisogenyapply(z[2],P);
S=concat(B,apply(v->ellneg(E,v),B)); T=apply(phi,S);
if(!prod(i=1,#T,ellisoncurve(F,T[i])),error("transported point"));
count=0; image=List();
{for(i=1,#S,for(j=i,#S,
    L=elladd(E,S[i],S[j]); M=elladd(F,T[i],T[j]);
    if(phi(L)!=M,error("pair"));
    count++; if(#M==2,listput(image,lift(M)))
));}
{for(i=1,#R,r=R[i];
    L=elladd(F,ellmul(F,phi(P),r[1]),ellmul(F,phi(Q),r[2]));
    M=elladd(F,ellmul(F,T[r[3]+1],r[5]),ellmul(F,T[r[4]+1],r[6]));
    if(L!=M,error("row"))
);}
print([ellcard(F),count,#Set(Vec(image)),#R]);
"""
    result = subprocess.run(["gp", "-q", "-f"], input=script, capture_output=True,
                            text=True, check=True)
    if result.stderr or result.stdout.strip() != "[2147505293, 595, 578, 78]":
        raise ValueError(f"Fixture replay mismatch: {result.stdout!r} {result.stderr!r}")
    print("Verified 595 pair sums, 578 distinct finite images and 78 saved equations.")


if __name__ == "__main__":
    main()
