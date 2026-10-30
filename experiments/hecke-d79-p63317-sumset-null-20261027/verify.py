"""Verify the frozen matched-null evidence and independent full replay."""
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
    inputs, pre, post = read('inputs.json'), read('pre-run.json'), read('post-run.json')
    result, audit, sealed = read('result.json'), read('audit.json'), read('post_audit.json')
    assert pre['inputs_sha256'] == sha(HERE / 'inputs.json')
    assert pre['protocol_sha256'] == sha(HERE / 'PROTOCOL.md')
    assert pre['producer_sha256'] == sha(HERE / 'run.py')
    for name, item in inputs['frozen'].items():
        assert sha(ROOT / item['path']) == item['sha256'] == pre['input_hashes'][name]
    assert post['pre_run_sha256'] == sha(HERE / 'pre-run.json')
    assert post['result_sha256'] == sha(HERE / 'result.json')
    assert post['audit_script_sha256'] == sha(HERE / 'audit.py')
    assert result['status'] == 'COMPLETE' and audit['status'] == 'PASS'
    assert result['observed']['triple_patterns'] == 79040
    assert result['observed']['triple_coverage'] == 2503
    assert result['observed']['fixed_translate_additional'] == 28
    assert result['observed']['fixed_translate_union'] == 2531
    assert audit['observed_metrics']['triple_coverage'] == 2503
    assert audit['draws_replayed'] == len(result['control_rows']) == 256
    assert all(len(row['orbit_representatives']) == len(set(row['orbit_representatives'])) == 19
               and row['triple_patterns'] == 79040 for row in result['control_rows'])
    assert result['summary']['triple_coverage_median'] == 2501
    assert result['summary']['triple_upper_tail_fraction'] == '123/257'
    assert result['summary']['triple_lower_tail_fraction'] == '144/257'
    assert result['summary']['full_union_draws'] == audit['control_full_union_draws'] == 198
    assert result['candidate_id'] is None and result['target_online_ms'] is None
    for name, expected in sealed['sha256'].items():
        assert sha(HERE / name) == expected, name
    print('PASS: frozen sign-orbit controls, 256 independent row replays and additive-null summary')


if __name__ == '__main__':
    main()
