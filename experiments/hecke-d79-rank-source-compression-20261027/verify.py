"""Verify frozen rank-source compression receipts and independent replay."""
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
    assert pre['retrospective_pilot_observed_five_source_p63317'] is True
    for name, item in inputs['frozen'].items():
        assert sha(ROOT / item['path']) == item['sha256'] == pre['input_hashes'][name]
    assert post['pre_run_sha256'] == sha(HERE / 'pre-run.json')
    assert post['result_sha256'] == sha(HERE / 'result.json')
    assert post['audit_script_sha256'] == sha(HERE / 'audit_sage.py')
    assert result['status'] == 'COMPLETE' and audit['status'] == 'PASS'
    cases = {x['p']:x for x in result['cases']}
    acases = {x['p']:x for x in audit['cases']}
    assert set(cases) == set(acases) == {63317,68437}
    a, b = cases[63317], cases[68437]
    assert (a['baseline_rank'],a['full_pool_rank'],a['selected_candidate_indices'],a['selected_sources']) == (37,39,[221,226],[17,18,23,33,36])
    assert a['tested_combinations'] == 27966 and a['four_source_union_pairs'] == 0
    assert a['selected_source_lift_ns'] == 198730292 and a['all_source_lift_ns'] == 1772592789
    assert acases[63317]['anchored_logs_recovered'] is True
    assert (b['baseline_rank'],b['full_pool_rank'],b['selected_candidate_indices'],b['remaining_rank_deficit']) == (33,34,[0],6)
    assert b['tested_combinations'] == 196 and acases[68437]['anchored_logs_recovered'] is False
    assert result['candidate_id'] is None and result['target_online_ms'] is None
    build = (HERE / 'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build
    assert build.count('does not depend on any axioms') == 4
    assert 'sorryAx' not in build
    source = (HERE / 'formal/RankSourceCompression.lean').read_text()
    assert 'sorry' not in source and 'admit' not in source
    for name, expected in sealed['sha256'].items():
        assert sha(HERE / name) == expected, name
    print('PASS: retrospective source minimum, Sage rank and log replay, Lean finite certificates')


if __name__ == '__main__':
    main()
