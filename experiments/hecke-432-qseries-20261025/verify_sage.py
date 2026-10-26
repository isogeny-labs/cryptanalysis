"""Independent checked-Sage replay of saved newform and parametrization data."""
from hashlib import sha256
import json
from pathlib import Path

from sage.all import EllipticCurve, Gamma0, O, QQ

HERE = Path(__file__).resolve().parent


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE/'protocol.json'
    result_path = HERE/'qseries_result.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    assert result['protocol_sha256'] == sha(protocol_path)
    curve = EllipticCurve(QQ, protocol['curve_ainvs'])
    assert int(curve.conductor()) == result['level'] == 432
    assert int(Gamma0(432).index()) == result['index'] == 864
    assert result['sturm_bound'] == 144
    form = curve.q_expansion(145)
    assert [int(form[n]) for n in range(145)] == result['newform_coefficients']
    x_series, y_series = curve.modular_parametrization().power_series(prec=50)
    assert {str(n): str(x_series[n]) for n in range(-2,40)} == result['parametrization_X_coefficients']
    assert {str(n): str(y_series[n]) for n in range(-3,40)} == result['parametrization_Y_coefficients']
    q = x_series.parent().gen()
    assert y_series**2-x_series**3+16+O(q**40) == 0
    assert x_series.derivative()/(2*y_series)+O(q**40) == form/q+O(q**40)
    output = {'status': 'PASS_INDEPENDENT_QSERIES_REPLAY',
              'protocol_sha256': sha(protocol_path),
              'qseries_result_sha256': sha(result_path),
              'newform_coefficients_checked': 145,
              'parametrization_exclusive_precision': 40,
              'curve_and_differential_identities_checked': True,
              'finite_field_evaluator': None}
    (HERE/'qseries_validation.json').write_text(json.dumps(output, sort_keys=True, indent=2)+'\n')
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
