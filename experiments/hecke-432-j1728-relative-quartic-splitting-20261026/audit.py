"""Audit immutable inputs and bounded direct-PARI attempt receipts."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    'factor_certificate': ROOT / 'experiments/hecke-432-j1728-resolvent-field-20261026/factor_certificate.json',
    'split_certificate': ROOT / 'experiments/hecke-432-j1728-sqrt2-split-20261026/sqrt2_factor_certificate.json',
    'local_order_support_result': ROOT / 'experiments/hecke-432-j1728-relative-quartic-local-order-20261026/conjugate_support_result.json',
}


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['primes'] == [7, 11, 23, 31]
    for name, path in INPUTS.items():
        assert sha256(path.read_bytes()).hexdigest() == protocol['input_sha256'][name]
    squarefree = json.loads((HERE / 'squarefree_result.json').read_text())
    source_path = HERE.parent / 'hecke-432-j1728-relative-quartic-local-order-20261026/result.json'
    assert squarefree['status'] == 'PASS_CERTIFIED_SQUAREFREE_COMPONENTS'
    assert squarefree['source_sha256'] == sha256(source_path.read_bytes()).hexdigest()
    assert [r['prime'] for r in squarefree['rows']] == protocol['primes']
    for row in squarefree['rows']:
        for side in ('left', 'right'):
            block = row['sides'][side]
            assert sum(d * n for d, n in block['certified_absolute_degree_counts']) + \
                block['unresolved_absolute_degree_mass'] == 144
            assert block['certified_absolute_prime_count'] == sum(
                n for _, n in block['certified_absolute_degree_counts'])
    receipts = {}
    for path in sorted(HERE.glob('attempt*.json')):
        receipt = json.loads(path.read_text())
        assert receipt['command'] == [str(ROOT / 'sage'), '-python', str(HERE / 'run_sage.py')]
        assert receipt['status'] in {'TIME_LIMIT', 'SAGE_ERROR', 'COMPLETED'}
        assert receipt['elapsed_seconds'] > 0
        if receipt['status'] == 'TIME_LIMIT':
            assert receipt['returncode'] is None
        receipts[path.name] = {'status': receipt['status'],
                               'elapsed_seconds': receipt['elapsed_seconds'],
                               'stdout_tail': receipt['stdout'][-400:]}
    result_path = HERE / 'result.json'
    if result_path.exists():
        result = json.loads(result_path.read_text())
        assert result['protocol_sha256'] == sha256((HERE / 'protocol.json').read_bytes()).hexdigest()
        assert [row['prime'] for row in result['rows']] == protocol['primes'][:len(result['rows'])]
        for row in result['rows']:
            assert sum(degree * count for degree, count in
                       row['absolute_residue_degree_counts']) == 144
            assert sum(count for _, count in row['relative_pattern_counts']) == len(row['base_places'])
        result_status = result['status']
        completed_primes = [row['prime'] for row in result['rows']]
    else:
        result_status = 'BOUNDED_UNKNOWN'
        completed_primes = []
    report = {'status': 'PASS_AUDIT', 'result_status': result_status,
              'completed_primes': completed_primes, 'receipts': receipts}
    (HERE / 'audit.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'result_status': result_status,
                      'completed_primes': completed_primes}, sort_keys=True))


if __name__ == '__main__':
    main()
