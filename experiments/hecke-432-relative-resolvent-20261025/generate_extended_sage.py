"""Generate checked two-prime q-series through exponent 2000."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, LaurentSeriesRing, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def reduce_series(series, field, ring, precision):
    q = ring.gen()
    out = ring.zero()
    for n in range(int(series.valuation()),min(int(series.prec()),precision)):
        if series[n]:
            out += field(QQ(series[n]))*q**n
    return out.add_bigoh(min(int(series.prec()),precision))


def main():
    protocol_path = HERE/'extension_protocol.json'
    old_path = ROOT/'hecke-432-full-e-lift-20261025'/'qseries_modp.json'
    protocol = json.loads(protocol_path.read_text())
    old = json.loads(old_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_EXTENDED_RELATIVE_RESOLVENT'
    precision = protocol['q_series_precision']
    C = EllipticCurve('27a1')
    B = EllipticCurve(QQ,[0,0,0,0,-16])
    xc,yc = C.modular_parametrization().power_series(precision)
    xb,yb = B.modular_parametrization().power_series(precision)
    source = []
    lo,hi = protocol['stored_coefficients']
    for original in old:
        p = original['prime']
        field = GF(p)
        ring = LaurentSeriesRing(field,'q')
        parts = {name:reduce_series(value,field,ring,precision)
                 for name,value in (('xc',xc),('yc',yc),('xb',xb),('yb',yb))}
        parts['hx'] = (parts['xb']**3-64)/parts['xb']**2
        parts['hy'] = parts['yb']*(parts['xb']**3+128)/parts['xb']**3
        assert min(s.prec() for s in parts.values()) > hi
        assert (parts['yc']**2+parts['yc']-parts['xc']**3+7).add_bigoh(1851) == 0
        assert (parts['yb']**2-parts['xb']**3+16).add_bigoh(1851) == 0
        assert (parts['hy']**2-parts['hx']**3-432).add_bigoh(1851) == 0
        row = {'prime':p,'coefficient_exponents':[lo,hi]}
        for name,series in parts.items():
            row[name] = [int(series[n]) for n in range(lo,hi+1)]
            assert row[name][:1054] == original[name]
        source.append(row)
        print(json.dumps({'prime':p,'minimum_precision':int(min(s.prec() for s in parts.values())),
                          'overlap_coefficients_per_function':1054}),flush=True)
    out = {'status':'COMPLETE_EXTENDED_QSERIES',
           'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
           'prior_source_sha256':sha256(old_path.read_bytes()).hexdigest(),
           'rows':source}
    (HERE/'qseries_extended.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'fields':len(source)},sort_keys=True))


if __name__=='__main__':
    main()
