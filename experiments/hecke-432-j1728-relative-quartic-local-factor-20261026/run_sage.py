"""Decompose one specified base place through a saved PARI relative field."""
import json
import time
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, pari

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    started = time.monotonic()

    def phase(name):
        print(json.dumps({'phase': name, 'elapsed_seconds': round(time.monotonic() - started, 3)},
                         sort_keys=True), flush=True)

    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {key: ROOT / path for key, path in protocol['input_paths'].items()}
    for key, path in paths.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][key]
    cert = json.loads(paths['factor_certificate'].read_text())
    screen = json.loads(paths['local_screen'].read_text())
    support = json.loads(paths['relative_discriminant_support'].read_text())
    assert support['status'] == 'PASS_CONJUGATE_RELATIVE_DISCRIMINANT_SUPPORT'
    p = protocol['rational_prime']
    i = protocol['base_place_index_in_local_screen']
    row = next(r for r in screen['rows'] if r['prime'] == p)
    saved_place = row['places'][i]
    assert saved_place['left']['reduced_factor_degrees_exponents'] == protocol['expected_reduction']
    support_row = next(r for r in support['rows'] if r['prime'] == p)
    assert support_row['places'][i]['left_relative_discriminant_valuation'] == 0
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    phase('relative_base_constructed')
    P = L.primes_above(p)[i]
    assert [str(x) for x in P.gens()] == saved_place['ideal_generators']
    f_base = int(P.residue_class_degree())
    e_base = int(P.absolute_ramification_index())
    assert f_base == saved_place['residue_degree'] and e_base == 1
    phase('base_prime_matched')
    pari.allocatemem(protocol['pari_stack_bytes'])
    prime = P.pari_prime()
    phase('pari_base_prime_ready')
    rnf = pari.read(str(paths['rnf_checkpoint']))
    phase('rnf_checkpoint_loaded')
    lifts = rnf.rnfidealprimedec(prime)
    phase('single_prime_decomposition_complete')
    rows = []
    for q in lifts:
        e_abs = int(q[2])
        f_abs = int(q[3])
        assert e_abs % e_base == 0 and f_abs % f_base == 0
        rows.append({'absolute_ramification_index': e_abs,
                     'absolute_residue_degree': f_abs,
                     'relative_ramification_index': e_abs // e_base,
                     'relative_residue_degree': f_abs // f_base})
    assert all(x['relative_ramification_index'] == 1 for x in rows)
    assert sum(x['relative_ramification_index'] * x['relative_residue_degree']
               for x in rows) == 4
    relative_degrees = sorted(x['relative_residue_degree'] for x in rows)
    assert relative_degrees in ([1, 1, 1, 1], [1, 1, 2])
    out = {'status': 'PASS_SINGLE_PLACE_RELATIVE_QUARTIC_DECOMPOSITION',
           'rational_prime': p, 'base_place_index_in_local_screen': i,
           'base_residue_degree': f_base,
           'base_ramification_index': e_base,
           'relative_residue_degrees': relative_degrees,
           'lifts': rows,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'relative_residue_degrees': relative_degrees},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
