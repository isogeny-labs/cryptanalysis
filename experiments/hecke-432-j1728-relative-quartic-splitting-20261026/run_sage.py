"""Direct PARI relative prime decomposition in the degree-144 field."""
import json
import os
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sage.all import NumberField, PolynomialRing, QQ, pari

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'local_order_support_result': ROOT / 'experiments/hecke-432-j1728-relative-quartic-local-order-20261026/conjugate_support_result.json',
}


def base_element(values, alpha, K):
    return sum((K(QQ(v)) * alpha ** i for i, v in enumerate(values)), K(0))


def relative_element(values, alpha, s, K, L):
    return sum((L(base_element(vector, alpha, K)) * s ** i
                for i, vector in enumerate(values)), L(0))


def save(rows, protocol_path, status):
    out = {'status': status, 'base_field_absolute_degree': 36,
           'extension_relative_degree': 4, 'field_absolute_degree': 144,
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


def main():
    def phase(name):
        print(json.dumps({'phase': name}, sort_keys=True), flush=True)

    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    cert = json.loads(INPUTS['factor_certificate'].read_text())
    split = json.loads(INPUTS['split_certificate'].read_text())
    support = json.loads(INPUTS['local_order_support_result'].read_text())
    assert support['status'] == 'PASS_CONJUGATE_RELATIVE_DISCRIMINANT_SUPPORT'
    Qx = PolynomialRing(QQ, 'x')
    K = NumberField(Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']]), 'alpha')
    phase('base_field_constructed')
    alpha = K.gen()
    Rt = PolynomialRing(K, 't')
    L = K.extension(Rt.gen() ** 2 - 2, 's')
    phase('relative_base_constructed')
    s = L.gen()
    Lz = PolynomialRing(L, 'z')
    octic = next(r for r in split['records'] if r['base_degree'] == 8)
    g = Lz([relative_element(v, alpha, s, K, L)
            for v in octic['factors'][0]['coefficients_low_to_high']])
    assert g.degree() == 4 and g.is_monic() and g.is_irreducible()
    phase('quartic_checked')
    checkpoint = HERE / 'rnf-checkpoint.bin'
    checkpoint_meta = HERE / 'rnf-checkpoint.json'
    pari.allocatemem(protocol['pari_stack_bytes'])
    if checkpoint.exists():
        meta = json.loads(checkpoint_meta.read_text())
        assert meta['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
        assert meta['binary_sha256'] == sha256(checkpoint.read_bytes()).hexdigest()
        rnf = pari.read(str(checkpoint))
        print(json.dumps({'phase': 'rnf_checkpoint_loaded', 'bytes': checkpoint.stat().st_size},
                         sort_keys=True), flush=True)
    else:
        phase('pari_nf_started')
        nf = L.pari_nf()
        phase('pari_nf_complete')
        polynomial = g._pari_with_name('x')
        phase('rnfinit_started')
        rnf = nf.rnfinit(polynomial)
        phase('rnfinit_complete')
        temporary = HERE / f'rnf-checkpoint-{os.getpid()}.bin'
        phase('checkpoint_write_started')
        pari.writebin(str(temporary), rnf)
        temporary.replace(checkpoint)
        meta = {'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
                'binary_sha256': sha256(checkpoint.read_bytes()).hexdigest(),
                'binary_bytes': checkpoint.stat().st_size,
                'format': 'PARI writebin; architecture dependent'}
        checkpoint_meta.write_text(json.dumps(meta, sort_keys=True, indent=2) + '\n')
        print(json.dumps({'phase': 'rnf_checkpoint_saved',
                          'bytes': checkpoint.stat().st_size}, sort_keys=True), flush=True)
    result_path = HERE / 'result.json'
    if result_path.exists():
        prior = json.loads(result_path.read_text())
        assert prior['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
        rows = prior['rows']
    else:
        rows = []
    completed = {row['prime'] for row in rows}
    for p in protocol['primes']:
        if p in completed:
            continue
        SK, SL = rnf.rnfidealprimedec(p)
        assert len(SK) == len(SL)
        base_places = []
        absolute_degrees = []
        for base_prime, above in zip(SK, SL):
            base_e, base_f = int(base_prime[2]), int(base_prime[3])
            assert base_e == 1
            lifts = []
            for q in above:
                e_abs, f_abs = int(q[2]), int(q[3])
                assert e_abs % base_e == 0 and f_abs % base_f == 0
                e_rel, f_rel = e_abs // base_e, f_abs // base_f
                assert e_rel == 1
                lifts.append({'absolute_ramification_index': e_abs,
                              'absolute_residue_degree': f_abs,
                              'relative_ramification_index': e_rel,
                              'relative_residue_degree': f_rel})
                absolute_degrees.extend([f_abs] * e_abs)
            assert sum(v['relative_ramification_index'] * v['relative_residue_degree']
                       for v in lifts) == 4
            base_places.append({'base_ramification_index': base_e,
                                'base_residue_degree': base_f,
                                'lifts': lifts,
                                'relative_residue_degree_pattern':
                                    sorted(v['relative_residue_degree'] for v in lifts)})
        assert sum(absolute_degrees) == 144
        assert sum(v['base_ramification_index'] * v['base_residue_degree']
                   for v in base_places) == 36
        degree_counts = Counter(absolute_degrees)
        rows.append({'prime': p, 'base_places': base_places,
                     'absolute_prime_count': sum(degree_counts.values()),
                     'absolute_residue_degree_counts':
                         [[int(degree), int(count)] for degree, count in sorted(degree_counts.items())],
                     'relative_pattern_counts':
                         [[list(pattern), count] for pattern, count in sorted(
                             Counter(tuple(v['relative_residue_degree_pattern'])
                                     for v in base_places).items())]})
        save(rows, protocol_path, 'PARTIAL_RELATIVE_QUARTIC_SPLITTING')
        print(json.dumps({'prime': p, 'absolute_prime_count': rows[-1]['absolute_prime_count'],
                          'degree_counts': rows[-1]['absolute_residue_degree_counts']},
                         sort_keys=True), flush=True)
    save(rows, protocol_path, 'PASS_RELATIVE_QUARTIC_PRIME_DECOMPOSITION')
    print(json.dumps({'status': 'PASS_RELATIVE_QUARTIC_PRIME_DECOMPOSITION'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
