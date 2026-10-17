"""Read-only terminal check of the split-minor source screen."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_rr_joint_box_rank_20261017'
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017/join_input.tsv'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    protocol = load(HERE / 'protocol.json')
    result = load(HERE / 'result.json')
    audit = load(HERE / 'audit_result.json')
    prior = load(PRIOR / 'result.json')
    assert protocol['status'] == 'FROZEN_N41_SPLIT_MINOR_AFFINE_SCREEN'
    assert protocol['source_sha256'] == {
        'runner': sha(HERE / 'run.py'), 'panel': sha(PRIOR / 'panel.json'),
        'source': sha(SOURCE), 'prior_result': sha(PRIOR / 'result.json')}
    assert protocol['panel_indices'] == [*range(32), *range(32, 36), *range(64, 97)]
    assert protocol['one_worker'] and protocol['wall_cap_seconds'] == 180
    assert result['status'] == 'COMPLETE' and len(result['rows']) == 69
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert 0 < result['elapsed_seconds'] < protocol['wall_cap_seconds']
    assert result['peak_self_rss_raw'] < protocol['rss_observational_boundary_bytes']
    counts = Counter(row['kind'] for row in result['rows'])
    assert counts == {'sign': 32, 'root_sign': 4, 'two_code': 32,
                      'witness_two_code': 1}
    assert sum(row['field_pairings'] for row in result['rows']) == 3675
    assert result['field_mul_calls'] == 3223177
    for row in result['rows']:
        old = prior['rows'][row['panel_index']]
        assert row['first_determinant'] == old['first_determinant']
        if row['kind'] == 'sign':
            assert row['status'] == 'CERTIFIED_NO_ZERO'
            assert row['field_difference_rank'] == 34
        else:
            assert row['status'] == 'NO_AFFINE_LINEAR_SEPARATOR'
            assert row['field_difference_rank'] == 41
    assert audit['status'] == 'PASS_INDEPENDENT_SPLIT_MINOR_AUDIT'
    assert audit['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert audit['result_sha256'] == sha(HERE / 'result.json')
    assert audit['prior_audit_sha256'] == sha(PRIOR / 'audit_result.json')
    assert audit['script_sha256'] == sha(HERE / 'audit.py')
    assert audit['boxes_checked'] == 69
    assert audit['certified_sign_values'] == 2048
    assert audit['independent_determinants'] == 3664
    assert audit['zero_determinants_seen'] == 1
    assert "'SplitCertificate.affine_bilinear_separation' depends on axioms: [propext]" \
        in (HERE / 'lean.stdout').read_text()
    assert '4.34.1' in (HERE / 'lean_version.txt').read_text()
    for marker in ('sorry', 'admit', 'sorryAx'):
        assert marker not in (HERE / 'SplitCertificate.lean').read_text()
    for name in ('freeze.stderr', 'run.stderr', 'audit.stderr', 'lean.stderr'):
        assert not (HERE / name).read_bytes()
    print('PASS_SPLIT_MINOR_TERMINAL_VERIFY',
          len(result['rows']), audit['independent_determinants'])


if __name__ == '__main__':
    main()
