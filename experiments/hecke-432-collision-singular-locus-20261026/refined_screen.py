"""Post hoc refinement after the frozen singular-only prediction failed."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    protocol_path = HERE/'refinement_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_AFTER_INITIAL_FAILURE_BEFORE_REFINED_REPLAY'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    rows = json.loads((HERE/'gradient_rows.json').read_text())
    assert len(rows) == 6120
    result = {'status': 'EXPLORATORY_REFINED_COLLISION_RULE',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'primes': {}}
    for p in protocol['prime_scope']:
        subset = [r for r in rows if r['prime'] == p]
        counts = Counter()
        mismatches = []
        for row in subset:
            y_zero = row['B_point'][1] == 0
            singular = row['dT'] == row['dC'] == 0
            double = row['multiplicity'] > 1
            counts[(singular, y_zero, double)] += 1
            if double != (singular or y_zero):
                mismatches.append(row)
        result['primes'][str(p)] = {'triples': len(subset),
                                   'classification': [
                                       {'singular': a, 'y_B_zero': b, 'double': c, 'count': n}
                                       for (a, b, c), n in sorted(counts.items())],
                                   'mismatches': mismatches}
        print(json.dumps({'prime': p, 'triples': len(subset),
                          'mismatches': len(mismatches),
                          'classification': result['primes'][str(p)]['classification']},
                         sort_keys=True), flush=True)
    result['total_triples'] = len(rows)
    result['total_mismatches'] = sum(len(r['mismatches']) for r in result['primes'].values())
    (HERE/'refined_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
