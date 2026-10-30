"""Bind frozen direct receipts, local-gcd output, and independent Sage audit."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'bad_prime_audit': ROOT / 'experiments/hecke-432-j1728-sqrt2-resultants-20261026/bad_prime_audit.json',
    'million_exception_result': ROOT / 'experiments/hecke-432-j1728-sqrt2-million-20261026/exception_result.json',
    'ten_million_exception_result': ROOT / 'experiments/hecke-432-j1728-octic-collision-holdout-20261026/exception_result.json',
}


def main():
    pp = HERE / 'protocol.json'
    protocol = json.loads(pp.read_text())
    rp = HERE / 'result.json'
    result = json.loads(rp.read_text())
    ap = HERE / 'audit.json'
    audit = json.loads(ap.read_text())
    assert result['status'] == 'PASS_FAST_LOCAL_GCD_REPLAY_OF_ELEVEN_EXCEPTIONS'
    assert audit['status'] == 'PASS_INDEPENDENT_SAGE_FAST_LOCAL_GATE_REPLAY'
    assert result['protocol_sha256'] == sha256(pp.read_bytes()).hexdigest()
    assert audit['audit_protocol_sha256'] == sha256((HERE / 'audit_protocol.json').read_bytes()).hexdigest()
    direct = {}
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
        for cell in json.loads(path.read_text())['cells']:
            direct[cell['prime']] = cell['rational_CE_pairs']
    assert sorted(direct) == sorted(protocol['prime_cells'])
    counts = {'source_points': 0, 'undefined_source_j_points': 0,
              'rational_x_E_roots': 0,
              'rational_CE_pairs': 0, 'polynomial_multiplications': 0,
              'polynomial_remainders': 0, 'polynomial_gcds': 0,
              'modular_exponentiations': 0, 'coefficient_product_terms': 0}
    maximum_multiplications = 0
    for cell, checked in zip(result['cells'], audit['audited_cells']):
        p = cell['prime']
        assert p == checked['prime']
        assert cell['rational_CE_pairs'] == checked['rational_CE_pairs'] == direct[p]
        assert len(cell['source_points']) == checked['source_points']
        counts['source_points'] += len(cell['source_points'])
        counts['undefined_source_j_points'] += len(cell['undefined_source_j_points'])
        counts['rational_CE_pairs'] += cell['rational_CE_pairs']
        for fiber in cell['fibers']:
            assert fiber['status'] == 'EXACT_LOCAL_POLYNOMIAL_GCD_GATE'
            counts['rational_x_E_roots'] += fiber['rational_x_E_roots']
            for key, value in fiber['arithmetic_counts'].items():
                counts[key] += value
            maximum_multiplications = max(
                maximum_multiplications,
                fiber['arithmetic_counts']['polynomial_multiplications'])
    assert counts['source_points'] == 22
    assert counts['undefined_source_j_points'] == 1
    assert counts['rational_CE_pairs'] == 14
    out = {'status': 'PASS_FAST_LOCAL_GCD_EVIDENCE',
           'protocol_sha256': sha256(pp.read_bytes()).hexdigest(),
           'result_sha256': sha256(rp.read_bytes()).hexdigest(),
           'audit_sha256': sha256(ap.read_bytes()).hexdigest(),
           'prime_cells': len(result['cells']),
           'aggregate_counts': counts,
           'max_polynomial_multiplications_per_source_fiber': maximum_multiplications}
    (HERE / 'validation.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
