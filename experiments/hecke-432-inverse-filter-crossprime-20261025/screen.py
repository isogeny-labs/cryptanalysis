"""Source-free complete rational inverse-filter screen at three primes."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from inverse_filter import curve_points, evaluate_pair, horner, resolvent_coefficients

HERE = Path(__file__).resolve().parent


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_CROSSPRIME_INVERSE_FILTER'
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    result = {'status': 'COMPLETE_CROSSPRIME_INVERSE_FILTER',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256((HERE/'inverse_filter.py').read_bytes()).hexdigest(),
              'primes': {}}
    for p in protocol['primes']:
        c_points, e_points = curve_points(p, 'C'), curve_points(p, 'E')
        e_by_x = defaultdict(list)
        for xe, ye in e_points:
            e_by_x[xe].append(ye)
        rows = []
        for c in c_points:
            coeffs = resolvent_coefficients(inputs['resolvent']['terms'], c, p)
            for xe, ys in e_by_x.items():
                if horner(coeffs, xe, p):
                    continue
                for ye in ys:
                    value = evaluate_pair(c, (xe, ye), p,
                                          inputs['resolvent'], inputs['branch'])
                    rows.append({'C_point': list(c), 'E_point': [xe, ye], **value})
        rows.sort(key=lambda row: (*row['C_point'], *row['E_point']))
        assert len(rows) == len({(*r['C_point'], *r['E_point']) for r in rows})
        shards = []
        for offset in range(0, len(rows), 250):
            path = HERE / f'p{p}-pairs-{offset//250:02d}.json'
            block = rows[offset:offset+250]
            path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
            shards.append({'file': path.name, 'rows': len(block),
                           'sha256': sha256(path.read_bytes()).hexdigest()})
        result['primes'][str(p)] = {'C_group_order': len(c_points)+1,
                                    'E_group_order': len(e_points)+1,
                                    'resolvent_pairs': len(rows),
                                    'status_histogram': dict(sorted(Counter(r['status'] for r in rows).items())),
                                    'pair_shards': shards}
        print(json.dumps({'prime': p, **{k: result['primes'][str(p)][k] for k in
                          ('resolvent_pairs', 'status_histogram')}}, sort_keys=True), flush=True)
    (HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
