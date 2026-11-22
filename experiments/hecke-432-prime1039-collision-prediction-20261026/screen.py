"""Prospective source-free rational C,E inverse screen at prime 1039."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_P1039_PROSPECTIVE_SCREEN'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    record = protocol['inputs']['inverse_filter']
    spec = importlib.util.spec_from_file_location('frozen_inverse_filter', record['path'])
    inverse = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inverse)
    resolvent = json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch = json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    p = protocol['prime']
    c_points, e_points = inverse.curve_points(p, 'C'), inverse.curve_points(p, 'E')
    e_by_x = defaultdict(list)
    for xe, ye in e_points:
        e_by_x[xe].append(ye)
    rows = []
    for c in c_points:
        coeffs = inverse.resolvent_coefficients(resolvent['terms'], c, p)
        for xe, ys in e_by_x.items():
            if inverse.horner(coeffs, xe, p):
                continue
            for ye in ys:
                value = inverse.evaluate_pair(c, (xe, ye), p, resolvent, branch)
                rows.append({'C_point': list(c), 'E_point': [xe, ye], **value})
    rows.sort(key=lambda row: (*row['C_point'], *row['E_point']))
    assert len(rows) == len({(*r['C_point'], *r['E_point']) for r in rows})
    shards = []
    for offset in range(0, len(rows), 250):
        path = HERE/f'pairs-{offset//250:02d}.json'
        block = rows[offset:offset+250]
        path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
        shards.append({'file': path.name, 'rows': len(block),
                       'sha256': sha256(path.read_bytes()).hexdigest()})
    result = {'status': 'COMPLETE_P1039_SOURCE_FREE_PAIR_SCREEN',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'C_group_order': len(c_points)+1, 'E_group_order': len(e_points)+1,
              'resolvent_pairs': len(rows),
              'status_histogram': dict(sorted(Counter(row['status'] for row in rows).items())),
              'shards': shards}
    (HERE/'screen_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('resolvent_pairs', 'status_histogram')}, sort_keys=True))


if __name__ == '__main__':
    main()
