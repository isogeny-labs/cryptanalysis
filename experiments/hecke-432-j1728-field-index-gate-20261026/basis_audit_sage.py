"""Verify the maximal-order discriminant using its explicit integral basis."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, ZZ, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    protocol_path = HERE / 'basis_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    result_path = HERE / 'result.json'
    assert sha256(result_path.read_bytes()).hexdigest() == protocol['input_result_sha256']
    result = json.loads(result_path.read_text())
    cert = json.loads((ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json').read_text())
    R = PolynomialRing(QQ, 'x')
    f = R([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']])
    K = NumberField(f, 'alpha')
    basis = [K(b) for b in K.maximal_order().basis()]
    assert len(basis) == 18
    trace = matrix(ZZ, 18, 18, [ZZ((basis[i] * basis[j]).trace())
                                for i in range(18) for j in range(18)])
    determinant = ZZ(trace.det())
    assert determinant == ZZ(result['field_discriminant'])
    coefficients = matrix(QQ, 18, 18, [QQ(basis[j].polynomial()[i])
                                        for i in range(18) for j in range(18)])
    change_det = QQ(coefficients.det())
    index = ZZ(result['order_index'])
    assert abs(change_det) * index == 1
    out = {'status': 'PASS_INTEGRAL_BASIS_TRACE_AND_INDEX',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'integral_basis_coefficients_power_basis':
               [[str(b.polynomial()[i]) for i in range(18)] for b in basis],
           'trace_determinant': str(determinant),
           'absolute_change_of_basis_determinant': str(abs(change_det)),
           'order_index': str(index)}
    (HERE / 'basis_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'field_discriminant': out['trace_determinant'],
                      'index_digits': len(str(index))}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
