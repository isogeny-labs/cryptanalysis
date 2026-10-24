"""Classify degree-2 modular-polynomial neighbors of disputed D=-35 roots."""
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, classical_modular_polynomial, hilbert_class_polynomial

HERE=Path(__file__).resolve().parent


def main():
    p=11131;d=35;F=GF(p);R=PolynomialRing(F,'J');J=R.gen()
    roots={c:{int(j) for j in hilbert_class_polynomial(-d*c*c).change_ring(F).roots(multiplicities=False)}
           for c in (1,2,3,6)}
    phi2=classical_modular_polynomial(2)
    rows=[]
    for source_c in (1,3):
        for j in sorted(roots[source_c]):
            neighbors=[{'j':int(z),'multiplicity':int(m),
                        'class_polynomial_memberships':[c for c in (1,2,3,6) if int(z) in roots[c]]}
                       for z,m in R(phi2(F(j),J)).roots()]
            rows.append({'source_j':j,'source_class_polynomial_conductor':source_c,
                         'neighbors':neighbors})
    out={'status':'DEGREE2_NEIGHBOR_STRATUM_DIAGNOSTIC','p':p,'d':d,'rows':rows}
    (HERE/'edge_diagnostic.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
