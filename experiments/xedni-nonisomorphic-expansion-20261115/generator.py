"""Check a screened rank-one point against Sage's proven generators."""
import json
import sys
from sage.all import EllipticCurve, QQ
p,u,x,y,B=map(int,sys.argv[1:6])
E=EllipticCurve(QQ,[-1,B])
P=E(x,y)
rank=int(E.rank(proof=True))
assert rank==1 and int(E.torsion_subgroup().order())==1
row={"field_prime":p,"u":u,"rank":rank,"torsion_order":1,
     "point":[x,y],"curve_B":B}
try:
    gens=list(E.gens(proof=True))
    row["generators"]=[list(map(str,G.xy())) for G in gens]
    row["generator_status"]="proved" if len(gens)==1 else "unexpected_count"
    if len(gens)==1:
        row["point_is_signed_generator"]=(P==gens[0] or P==-gens[0])
        row["point_index_up_to_20"]=next((i for i in range(1,21)
            if P==i*gens[0] or P==-i*gens[0]),None)
except Exception as exc:
    row["generator_status"]="error"
    row["generator_error"]=type(exc).__name__+": "+str(exc)[:200]
print(json.dumps(row,sort_keys=True))
