"""Audit frozen input identities and exact resolvent/Kummer witness receipts."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    return json.loads((HERE / name).read_text())


def digest(name):
    return sha256((HERE / name).read_bytes()).hexdigest()


def main():
    protocol = load('protocol.json')
    for name, relative in protocol['input_paths'].items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == protocol['input_sha256'][name]
    runtime = load('sage-runtime-info.txt')
    assert runtime['status'] == 'verified'
    attempt = load('attempt.json')
    result = load('result.json')
    assert attempt['status'] == 'COMPLETED' and attempt['returncode'] == 0
    assert attempt['source_sha256'] == digest('run_sage.py')
    assert result['status'] == 'PASS_CUBIC_RESOLVENT_GALOIS_CLASSIFICATION'
    assert result['protocol_sha256'] == digest('protocol.json')
    assert [(r['side'], r['galois_group_over_L'], r['cubic_factor_degrees'])
            for r in result['rows']] == [('left', 'V4', [1, 1, 1]),
                                          ('right', 'V4', [1, 1, 1])]
    kummer_protocol = load('kummer_protocol.json')
    for name, relative in kummer_protocol['input_paths'].items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == kummer_protocol['input_sha256'][name]
    kummer_attempt = load('kummer_attempt.json')
    kummer = load('kummer_result.json')
    assert kummer_attempt['status'] == 'COMPLETED' and kummer_attempt['returncode'] == 0
    assert kummer_attempt['source_sha256'] == digest('kummer_sage.py')
    assert kummer['status'] == 'PASS_KUMMER_SQUARE_CLASS_TEST'
    assert kummer['protocol_sha256'] == digest('kummer_protocol.json')
    for row in kummer['rows']:
        assert row['distinct_resolvent_roots_replayed']
        assert row['individual_square_flags'] == [False, False, False]
        assert len(row['pair_square_flags']) == 3
        assert not any(p['square'] for p in row['pair_square_flags'])
        assert row['triple_square'] and row['kummer_rank_two']
        assert len(row['triple_square_root_coefficients']) == 2
        assert all(len(v) == 18 for v in row['triple_square_root_coefficients'])
    assert [r['side'] for r in kummer['rows']] == ['left', 'right']
    replay = load('replay.json')
    assert replay['status'] == 'PASS_SERIALIZED_KUMMER_WITNESS_REPLAY'
    assert replay['kummer_result_sha256'] == digest('kummer_result.json')
    assert all(all(value for key, value in check.items() if key != 'side')
               for check in replay['checks'])
    out = {'status': 'PASS_RESOLVENT_KUMMER_AUDIT',
           'groups': {'left': 'V4', 'right': 'V4'},
           'kummer_rank': {'left': 2, 'right': 2},
           'result_sha256': digest('result.json'),
           'kummer_result_sha256': digest('kummer_result.json'),
           'replay_sha256': digest('replay.json')}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
