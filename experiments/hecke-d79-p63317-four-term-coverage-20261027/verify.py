"""Verify frozen inputs, complete residual rows, audit and Lean receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    plan, pre, post = read('inputs.json'), read('pre-run.json'), read('post-run.json')
    result, audit = read('result.json'), read('audit.json')
    assert pre['inputs_sha256'] == sha(HERE / 'inputs.json')
    assert pre['protocol_sha256'] == sha(HERE / 'PROTOCOL.md')
    assert pre['producer_sha256'] == sha(HERE / 'run.py')
    for name, item in plan['frozen'].items():
        assert sha(ROOT / item['path']) == item['sha256'] == pre['input_hashes'][name]
    assert post['pre_run_sha256'] == sha(HERE / 'pre-run.json')
    assert post['result_sha256'] == sha(HERE / 'result.json')
    assert post['audit_script_sha256'] == sha(HERE / 'audit_sage.py')
    assert result['status'] == 'ALL_RESIDUALS_FOUND' and audit['status'] == 'PASS'
    assert result['triple_patterns'] == 79040 and result['triple_coverage_points'] == 2503
    assert len(result['triple_residual_scalars']) == len(result['residual_rows']) == 28
    assert result['triple_residual_scalars'] == audit['triple_residual_scalars']
    assert all(x['status'] == 'FOUND' and x['probes'] == 1 and x['witness'][6:] == [0, -1]
               for x in result['residual_rows'])
    assert audit['residuals_verified_by_group'] == 28
    assert result['four_patterns'] == audit['four_patterns'] == 1462240
    assert result['four_coverage_points'] == audit['four_coverage_points'] == result['q'] == 2531
    assert result['four_uncovered_scalars'] == []
    assert result['candidate_id'] is None and result['target_online_ms'] is None
    build = (HERE / 'formal/build-output.txt').read_text()
    assert ('Built FourTermCoverage' in build or 'Replayed FourTermCoverage' in build)
    assert 'Build completed successfully' in build and 'does not depend on any axioms' in build
    assert build.count('does not depend on any axioms') == 29
    assert 'all_scalars_have_four_distinct_sources' in build
    assert 'sorryAx' not in build
    for name in ('FourTermCoverage.lean', 'FourTermCoverageChunks.lean'):
        source = (HERE / 'formal' / name).read_text()
        assert 'sorry' not in source and 'admit' not in source
    receipt = read('post_audit.json')
    for name, expected in receipt['sha256'].items():
        assert sha(HERE / name) == expected, name
    print('PASS: 28 first-probe residual witnesses, Sage group replay, complete four-source coverage and Lean certificates')


if __name__ == '__main__':
    main()
