"""Embed exact two-bit certificate multipliers into three-bit row orders."""
import hashlib
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def factors(variables):
    return [0] + [1 << bit for bit in range(variables)] + [
        (1 << a) | (1 << b) for a, b in combinations(range(variables), 2)]


def source_factors(path):
    lines = Path(path).read_text().splitlines()
    terminal = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    cert = [line for line in lines if line.startswith('CERT_ROWS')]
    assert len(terminal) == len(cert) == 1
    pairs = [tuple(map(int, pair.split(':'))) for pair in cert[0].split()[1:]]
    assert len(pairs) == int(terminal[0].split()[4])
    return sorted({factor for _, factor in pairs})


def lift(mask):
    return (mask & 3) | ((mask >> 2) << 3)


def main():
    cfg = json.loads((HERE / 'schedule_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_CERTIFICATE_GUIDED_ORDER'
    assert cfg['source_width'] == 2 and cfg['target_width'] == 3
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['sources'].values():
        assert sha(rec['path']) == rec['sha256']
    outputs = []
    for item in cfg['cases']:
        variables = item['variables']
        baseline = factors(variables)
        position = {mask: index for index, mask in enumerate(baseline)}
        source = source_factors(item['certificate_path'])
        seeded = {lift(mask) for mask in source}
        assert all(mask in position for mask in seeded)
        new_bit = 1 << 2
        extensions = {mask | new_bit for mask in seeded if mask.bit_count() <= 1}
        assert all(mask in position for mask in extensions)
        first = sorted(seeded, key=position.get)
        second = sorted(extensions - seeded, key=position.get)
        selected = set(first) | set(second)
        order = first + second + [mask for mask in baseline if mask not in selected]
        assert len(order) == len(baseline) and set(order) == set(baseline)
        path = HERE / item['output']
        with path.open('x') as stream:
            stream.write(f'FACTOR_ORDER {variables} {len(order)}\n')
            stream.writelines(f'{mask}\n' for mask in order)
        outputs.append({'case': item['case'], 'variables': variables,
                        'source_factors': len(source), 'lifted_factors': len(first),
                        'new_bit_extensions': len(second),
                        'total_factors': len(order), 'path': str(path),
                        'sha256': sha(path)})
    result = {'status': 'PASS_CERTIFICATE_GUIDED_SCHEDULES', 'candidate_id': None,
              'outputs': outputs,
              'protocol_sha256': sha(HERE / 'schedule_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'schedule_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
