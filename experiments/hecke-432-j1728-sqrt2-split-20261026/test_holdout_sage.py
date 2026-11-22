"""Prospective Frobenius-swap and coprimality test at fresh primes."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import GF, PolynomialRing

from check_certificate_sage import finite_eval, q_eval

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    pp=HERE/'holdout_protocol.json';protocol=json.loads(pp.read_text())
    sp=HERE/'holdout_selection.json';selection=json.loads(sp.read_text())
    assert selection['status']=='SELECTED_THREE_SQRT2_FROBENIUS_PRIMES'
    assert selection['protocol_sha256']==sha256(pp.read_bytes()).hexdigest()
    cp=Path(protocol['inputs']['sqrt2_certificate']['path']);cert=json.loads(cp.read_text())
    assert sha256(cp.read_bytes()).hexdigest()==protocol['inputs']['sqrt2_certificate']['sha256']
    base_path=Path(json.loads((HERE/'protocol.json').read_text())['input']['path'])
    base=json.loads(base_path.read_text())
    assert cert['source_certificate_sha256']==sha256(base_path.read_bytes()).hexdigest()
    resolvent_path=ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    terms=json.loads(resolvent_path.read_text())['terms']
    rows=[]
    for cell in selection['selected']:
        p=cell['prime'];F=GF(p);assert not F(2).is_square()
        E=GF(p*p,'u');s=E(2).sqrt();assert s**p==-s
        Fz=PolynomialRing(F,'z');z=Fz.gen()
        Ez=PolynomialRing(E,'z')
        for xc,yc in cell['C_points']:
            base_factors=[];pair_degrees=[]
            for source,record in zip(base['factors'],cert['records']):
                source_poly=Fz([q_eval(v,F(xc),F) for v in source['coefficients_low_to_high']])
                unit=finite_eval(record['unit'],E(xc),s,E)
                pair=[Ez([finite_eval(v,E(xc),s,E) for v in part['coefficients_low_to_high']])
                      for part in record['factors']]
                assert unit*pair[0]*pair[1]==Ez(source_poly)
                assert pair[0].gcd(pair[1]).degree()==0
                assert Ez([c**p for c in pair[0].list()]).monic()==pair[1].monic()
                assert Ez([c**p for c in pair[1].list()]).monic()==pair[0].monic()
                assert not source_poly.roots(multiplicities=False)
                base_factors.append(source_poly)
                pair_degrees.append([int(q.degree()) for q in pair])
            direct=Fz.zero()
            for term in terms:
                direct+=F(int(term['integer_coefficient']))*F(xc)**term['x_C_exponent']*F(yc)**term['y_C_exponent']*z**term['x_E_exponent']
            base_unit=base['unit']
            assert q_eval(base_unit,F(xc),F)*base_factors[0]*base_factors[1]==direct
            assert not direct.roots(multiplicities=False)
            rows.append({'prime':p,'C_point':[xc,yc],'pair_degrees':pair_degrees,
                         'frobenius_swap':True,'pairwise_coprime':True,
                         'rational_CE_pairs':0,'prediction_pass':True})
        print(json.dumps({'prime':p,'C_points':len(cell['C_points']),'prediction_pass':True}),flush=True)
    out={'status':'PASS_PROSPECTIVE_SQRT2_FROBENIUS_HOLDOUT' if len(rows)==6 and all(r['prediction_pass'] for r in rows) else 'FAIL_PROSPECTIVE_SQRT2_FROBENIUS_HOLDOUT',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'selection_sha256':sha256(sp.read_bytes()).hexdigest(),
         'certificate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'resolvent_sha256':sha256(resolvent_path.read_bytes()).hexdigest(),
         'rows':rows}
    (HERE/'holdout_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'rows':len(rows)}))


if __name__=='__main__':main()
