"""Pin the level-432 newform and modular-parametrization Laurent series."""
from hashlib import sha256
import json
from pathlib import Path
import time

from sage.all import EllipticCurve, Gamma0, O, QQ

HERE = Path(__file__).resolve().parent


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_PERSISTED_QSERIES_AND_ETA_SCREEN'
    curve = EllipticCurve(QQ, protocol['curve_ainvs'])
    assert curve.is_minimal() and int(curve.conductor()) == protocol['level']
    index = int(Gamma0(protocol['level']).index())
    sturm_bound = index*protocol['weight']//12
    assert index == 864 and sturm_bound == 144

    start = time.monotonic_ns()
    form = curve.q_expansion(protocol['newform_precision'])
    form_ns = time.monotonic_ns()-start
    assert form[1] == 1 and form[7] == 1 and form[13] == 5
    start = time.monotonic_ns()
    x_series, y_series = curve.modular_parametrization().power_series(
        prec=protocol['parametrization_precision'])
    map_ns = time.monotonic_ns()-start
    q = x_series.parent().gen()
    cap = protocol['equation_and_differential_check_precision']
    assert y_series**2-x_series**3+16+O(q**cap) == 0
    assert x_series.derivative()/(2*y_series)+O(q**cap) == form/q+O(q**cap)
    output = {
        'status': 'PASS_LEVEL432_MODULAR_QSERIES',
        'protocol_sha256': sha(protocol_path),
        'producer_sha256': sha(HERE/'produce_sage.py'),
        'curve_ainvs': protocol['curve_ainvs'],
        'level': protocol['level'], 'index': index, 'sturm_bound': sturm_bound,
        'newform_coefficients': [int(form[n]) for n in range(protocol['newform_precision'])],
        'parametrization_X_coefficients': {str(n): str(x_series[n]) for n in range(-2, cap)},
        'parametrization_Y_coefficients': {str(n): str(y_series[n]) for n in range(-3, cap)},
        'curve_equation_verified_through_q_exclusive': cap,
        'differential_identity_verified_through_q_exclusive': cap,
        'phase_wall_ns_diagnostic': {'newform': form_ns, 'parametrization': map_ns},
        'finite_field_evaluator': None,
        'candidate_id': None, 'timing_claim': None,
    }
    (HERE/'qseries_result.json').write_text(json.dumps(output, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': output['status'], 'sturm_bound': sturm_bound,
                      'q7_coefficient': output['newform_coefficients'][7],
                      'map_precision': cap}, sort_keys=True))


if __name__ == '__main__':
    main()
