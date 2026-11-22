"""Independently evaluate the frozen N131 positive witness in every equation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'witness_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_N131_WITNESS_GATE'
    assert cfg['witness'] == {'left_code': 3, 'right_code': 16722}
    assert sha(__file__) == cfg['script_sha256']
    for rec in cfg['dependencies'].values():
        assert sha(rec['path']) == rec['sha256']
    rec = cfg['positive_equations']
    assert sha(rec['path']) == rec['sha256']
    assignment = cfg['witness']['left_code'] | (cfg['witness']['right_code'] << 2)
    failures = []
    with Path(rec['path']).open() as stream:
        assert stream.readline().split() == ['EQS', '34', '131', '4', '2']
        for bit in range(131):
            line = [int(x) for x in stream.readline().split()]
            assert line[0] == bit and line[1] == len(line) - 2
            assert line[2:] == sorted(set(line[2:]))
            value = sum(1 for mask in line[2:] if mask & assignment == mask) & 1
            if value:
                failures.append(bit)
        assert not stream.read().strip()
    assert not failures
    result = {'status': 'PASS_N131_POSITIVE_WITNESS', 'candidate_id': None,
              'curve_id': cfg['curve_id'], 'witness': cfg['witness'],
              'field_coordinates_checked': 131,
              'positive_equations_sha256': rec['sha256'],
              'protocol_sha256': sha(HERE / 'witness_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'witness_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
