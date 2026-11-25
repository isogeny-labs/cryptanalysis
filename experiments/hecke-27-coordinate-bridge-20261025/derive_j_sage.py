"""Find the two rational j-maps on the optimal X0(27) model from q-series."""
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ, matrix
from sage.modular.modform.j_invariant import j_invariant_qexp

HERE = Path(__file__).resolve().parent


def basis(x, y, bound):
    out = []
    for b in (0, 1):
        for a in range((bound - 3*b)//2 + 1):
            out.append((a, b, x**a * y**b))
    return out


def derive(x, y, j, pole_j, bounds):
    for bound in bounds:
        aa = basis(x, y, bound)
        bb = basis(x, y, bound + pole_j)
        series = [term*j for _, _, term in aa] + [term for _, _, term in bb]
        lo, hi = -(bound+pole_j), 60
        mat = matrix(QQ, [[s[k] for s in series] for k in range(lo, hi)])
        kernel = mat.right_kernel()
        print('pole', pole_j, 'bound', bound, 'shape', mat.nrows(), mat.ncols(),
              'nullity', kernel.dimension(), flush=True)
        if kernel.dimension() == 1:
            v = kernel.basis()[0]
            combo = sum(v[k]*s for k, s in enumerate(series))
            assert all(combo[k] == 0 for k in range(60, 108))
            def terms(group, offset):
                return [{'x_power': a, 'y_power': b, 'coefficient': str(v[offset+k])}
                        for k, (a,b,_) in enumerate(group) if v[offset+k]]
            return {'denominator_pole_at_infinity': bound,
                    'j_pole_at_infinity': pole_j,
                    'numerator_pole_at_infinity': bound+pole_j,
                    'identity_form': 'denominator*j + numerator = 0',
                    'denominator': terms(aa, 0), 'numerator': terms(bb, len(aa)),
                    'q_training_exponents': [lo,hi-1],
                    'q_holdout_exponents': [60,107],
                    'training_nullity': 1, 'holdout_zero': True}
    raise RuntimeError('no unique rational function found')


def main():
    curve = EllipticCurve('27a1')
    x, y = curve.modular_parametrization().power_series(170)
    j_source = j_invariant_qexp(170)
    q = x.parent().gen()
    j_small = j_invariant_qexp(6)
    j_target = sum(j_small[k]*q**(27*k) for k in range(-1, 6))
    source = derive(x,y,j_source,1,[34,35])
    target = derive(x,y,j_target,27,[8,9,10,11])
    out = {'curve_label':'27a1', 'curve_ainvs':[int(c) for c in curve.ainvs()],
           'source_j':source, 'target_j':target}
    (HERE/'coordinate_map.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'source_terms':len(source['denominator'])+len(source['numerator']),
                      'target_terms':len(target['denominator'])+len(target['numerator']),
                      'source_pole':source['denominator_pole_at_infinity'],
                      'target_pole':target['denominator_pole_at_infinity']}), flush=True)


if __name__ == '__main__':
    main()
