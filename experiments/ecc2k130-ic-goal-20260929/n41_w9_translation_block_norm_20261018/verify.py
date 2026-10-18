"""Read-only verification of the translated block-norm evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    for name in ('prototype_protocol.json', 'sweep_protocol.json',
                 'audit_protocol.json'):
        protocol = load(name)
        for source, expected in protocol['source_sha256'].items():
            path = Path(source)
            if not path.is_absolute():
                path = ROOT / path
            assert sha(path) == expected, source
    first = load('first_failure.json')
    assert first['status'] == 'PRODUCER_FAILURE_SERIALIZATION'
    assert first['result_written'] is False
    prototype = load('prototype_result.json')
    assert prototype['status'] == 'PASS_THREE_BLOCK_CONTROLS'
    assert prototype['candidate_id'] is None
    assert prototype['source_sha256'] == sha(HERE / 'prototype_sage.py')
    assert prototype['first_failure_sha256'] == sha(HERE / 'first_failure.json')
    assert [(row['panel_index'], row['status'], row['gcd_degree'])
            for row in prototype['results']] == [
                (0, 'RETAIN', 1), (1, 'REJECT', 0), (2, 'REJECT', 0)]
    sweep = load('sweep_result.json')
    assert sweep['status'] == 'PASS_WIDTH_SWEEP_CONTROLS'
    assert sweep['candidate_id'] is None
    assert sweep['source_sha256'] == sha(HERE / 'sweep_sage.py')
    assert sweep['prototype_result_sha256'] == sha(HERE / 'prototype_result.json')
    assert sweep['widths'] == [1, 2, 4, 8, 16, 32]
    assert len(sweep['results']) == 18
    for width in sweep['widths']:
        rows = [row for row in sweep['results'] if row['width'] == width]
        assert [row['panel_index'] for row in rows] == [0, 1, 2]
        assert [row['status'] for row in rows] == ['RETAIN', 'REJECT', 'REJECT']
        assert [row['gcd_degree'] for row in rows] == [1, 0, 0]
        assert all((row['gcd_degree'] > 0) == bool(row['direct_candidates'])
                   for row in rows)
    audit = load('audit_result.json')
    assert audit['status'] == 'PASS_INTEGER_FIELD_BLOCK_NORM_ZERO_SETS'
    assert audit['tested_blocks'] == 18
    assert audit['sweep_result_sha256'] == sha(HERE / 'sweep_result.json')
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['auditor_sha256'] == sha(HERE / 'audit_integer.py')
    text = (HERE / 'lean.stdout').read_text()
    for name in ('conjugate_product', 'norm_nonzero_excludes_branches',
                 'bezout_rejects_both_branches'):
        assert f'TranslationBlockNorm.{name}' in text
    assert 'sorryAx' not in text and not (HERE / 'lean.stderr').read_bytes()
    assert 'sorryAx' in (HERE / 'lean_v1.stdout').read_text()
    print(json.dumps({'status': 'PASS_N41_TRANSLATED_BLOCK_NORM_RECEIPTS',
                      'tested_blocks': audit['tested_blocks'],
                      'widths': sweep['widths'],
                      'positive_retained_at_every_width': True}, sort_keys=True))


if __name__ == '__main__':
    main()
