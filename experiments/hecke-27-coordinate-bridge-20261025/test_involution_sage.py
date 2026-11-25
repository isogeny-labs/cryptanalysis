"""Identify the rational 27-Atkin-Lehner involution from the two j-maps."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent


def value(terms,P):
    field=P.curve().base_field()
    return sum(field(QQ(t['coefficient']))*P[0]**t['x_power']*P[1]**t['y_power']
               for t in terms)


def jval(mapping,P):
    if P.is_zero():
        return None
    den=value(mapping['denominator'],P)
    return None if den==0 else -value(mapping['numerator'],P)/den


def main():
    maps=json.loads((HERE/'coordinate_map.json').read_text())
    C=EllipticCurve(GF(877),maps['curve_ainvs'])
    trials=[]
    for torsion in (C(0),C(3,4),C(3,-5)):
        checked=matched=0
        for P in C.points():
            a=jval(maps['source_j'],P)
            b=jval(maps['target_j'],torsion-P)
            if a is None or b is None:
                continue
            checked+=1
            matched+=int(a==b)
        trials.append({'torsion':'O' if torsion.is_zero() else [int(torsion[0]),int(torsion[1])],
                       'checked':checked,'matched':matched})
    (HERE/'involution_probe.json').write_text(json.dumps(trials,sort_keys=True,indent=2)+'\n')
    print(json.dumps(trials,sort_keys=True))


if __name__=='__main__':
    main()
