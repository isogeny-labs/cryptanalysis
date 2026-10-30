"""Classify complete fibers using the C×B restricted Jacobian."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    protocol_path = HERE/'jacobian_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_RESTRICTED_JACOBIAN_REPLAY'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    rows = json.loads((HERE/'gradient_rows.json').read_text())
    out = {'status': 'EXPLORATORY_RESTRICTED_JACOBIAN_RULE',
           'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
           'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
           'primes': {}}
    for p in protocol['scope']:
        selected = [r for r in rows if r['prime'] == p]
        counts = Counter()
        mismatches = []
        for row in selected:
            db = (2*row['B_point'][1]*row['dT']) % p
            critical = row['dC'] == 0 and db == 0
            double = row['multiplicity'] > 1
            counts[(row['dC'] == 0, db == 0, double)] += 1
            if critical != double:
                mismatches.append({'C_point': row['C_point'], 'E_point': row['E_point'],
                                   'B_point': row['B_point'], 'dC': row['dC'],
                                   'restricted_B_derivative': db,
                                   'multiplicity': row['multiplicity']})
        out['primes'][str(p)] = {'triples': len(selected),
                                'classification': [
                                    {'C_derivative_zero': a, 'B_derivative_zero': b,
                                     'double': c, 'count': n}
                                    for (a, b, c), n in sorted(counts.items())],
                                'mismatches': mismatches}
        print(json.dumps({'prime': p, 'triples': len(selected),
                          'mismatches': len(mismatches),
                          'classification': out['primes'][str(p)]['classification']},
                         sort_keys=True), flush=True)
    out['total_triples'] = len(rows)
    out['total_mismatches'] = sum(len(r['mismatches']) for r in out['primes'].values())
    (HERE/'jacobian_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
