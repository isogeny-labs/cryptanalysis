"""Fail-closed terminal replay of the aligned-rotation stage evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
TRACE = ROOT / 'n41_n131_trace_parity_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


prepared = read('prepare_result.json')
assert prepared['status'] == 'PASS_PAIRED_ALIGNED_N41_INPUT'
assert prepared['source_sha256']['aligned_input'] == sha(HERE / 'aligned_input.tsv')
assert prepared['source_sha256']['aligned_states'] == sha(HERE / 'aligned_states.json')
assert prepared['source_sha256']['template_input'] == sha(PRIOR / 'join_input.tsv')
assert prepared['source_sha256']['template_states'] == sha(PRIOR / 'n41_states.json')

protocol = read('n41_protocol.json')
native = read('n41_result.json')
audit = read('n41_audit_result.json')
assert native['status'] == 'HIT_PENDING_SAGE_REPLAY'
assert native['protocol_sha256'] == sha(HERE / 'n41_protocol.json')
assert native['stdout_sha256'] == sha(HERE / 'n41.stdout')
assert native['stderr_sha256'] == sha(HERE / 'n41.stderr')
assert native['exit_code'] == 0 and native['stop_reason'] is None
assert len(native['hit_lines']) == 1
assert audit['status'] == 'PASS_INDEPENDENT_N41_ALIGNED_PUBLIC_RELATION'
assert audit['orientation'] == 6 and audit['state_ids'] == [105, 244, 66, 47, 111]
assert audit['distinct_folded_columns'] == 10
assert audit['search_result_sha256'] == sha(HERE / 'n41_result.json')
assert audit['source_sha256'] == sha(HERE / 'aligned_states.json')
for name, path in {'preparer': HERE / 'prepare_n41.py',
                   'prepared': HERE / 'prepare_result.json',
                   'states': HERE / 'aligned_states.json',
                   'input': HERE / 'aligned_input.tsv',
                   'runner': HERE / 'run_n41.py',
                   'native_source': PRIOR / 'join_orbit.cpp',
                   'native_binary': PRIOR / 'join_orbit',
                   'sage_runtime': HERE / 'sage_runtime_info.json'}.items():
    assert protocol['source_sha256'][name] == sha(path), name

rank_protocol = read('branch_rank_protocol.json')
rank = read('branch_rank_result.json')
rank_audit = read('branch_rank_audit.json')
assert rank['status'] == 'PASS_EXACT_BRANCH_DIFFERENCE_RANKS'
assert rank['protocol_sha256'] == sha(HERE / 'branch_rank_protocol.json')
assert rank_audit['status'] == 'PASS_INDEPENDENT_BRANCH_SPAN_RANKS'
assert rank_audit['producer_result_sha256'] == sha(HERE / 'branch_rank_result.json')
assert rank_audit['n41_pair_root_difference_edges'] == 71
assert [rank['rows'][name]['cases']['aligned']['annihilator_dimension']
        for name in ('n41', 'n131')] == [17, 47]
assert [rank['rows'][name]['cases']['original']['annihilator_dimension']
        for name in ('n41', 'n131')] == [1, 1]
assert rank_protocol['source_sha256']['script'] == sha(HERE / 'rank_branch_spans.py')

n41_build = read('build_n41_result.json')
ordered_build = read('build_n41_ordered_result.json')
n131_build = read('build_n131_result.json')
assert n41_build['status'] == 'PASS_N41_ALIGNED_MODEL_AND_MATCHED_FORMULAS'
assert ordered_build['status'] == 'PASS_N41_ALIGNED_ORDERED_MODEL'
assert n131_build['status'] == 'PASS_N131_ALIGNED_CONSTRUCTED_AND_PUBLIC_FORMULA'
for variant in ('original', 'aligned'):
    assert n41_build['rows'][variant]['formula_sha256'] == sha(HERE / f'n41_{variant}.xcnf')
assert ordered_build['formula_sha256'] == sha(HERE / 'n41_aligned_ordered.xcnf')
assert n131_build['formula_sha256'] == sha(HERE / 'n131_aligned_trace.xcnf')
assert n131_build['original_formula_sha256'] == sha(TRACE / 'n131_trace.xcnf')
assert n41_build['rows']['aligned']['assignment_check']['clauses'] == 45734
assert ordered_build['assignment_check']['clauses'] == 45868
assert n131_build['constructed_assignment_check']['clauses'] == 232430

probe_counts = {}
for field, expected_order, target_conflicts in (
        ('n41', ['original', 'aligned', 'ordered', 'ordered', 'aligned', 'original'], '50001'),
        ('n131', ['original', 'aligned', 'aligned', 'original'], '100001')):
    p = read(f'probe_{field}_protocol.json')
    result = read(f'probe_{field}_result.json')
    assert result['protocol_sha256'] == sha(HERE / f'probe_{field}_protocol.json')
    assert [row['variant'] for row in result['rows']] == expected_order == p['order']
    assert p['worker_count'] == 1 and p['combined_rss_cap_bytes'] == 4 * 1024**3
    assert p['source_sha256']['script'] == sha(HERE / f'probe_{field}.py')
    for row in result['rows']:
        index, variant = row['index'], row['variant']
        assert row['stdout_sha256'] == sha(HERE / f'probe_{field}_{index}_{variant}.stdout')
        assert row['stderr_sha256'] == sha(HERE / f'probe_{field}_{index}_{variant}.stderr')
        assert row['formula_sha256'] == p['source_sha256'][f'{variant}_formula']
        assert row['sampled_peak_combined_rss_bytes'] < 4 * 1024**3
        if field == 'n131' and index == 1:
            assert row['stop_reason'] == 'WALL_CAP' and not row['status_lines']
            assert row['conflicts'] is None
        else:
            assert row['stop_reason'] is None and row['exit_code'] == 0
            assert row['status_lines'] == ['s INDETERMINATE']
            assert row['conflicts'] == target_conflicts
    probe_counts[field] = len(result['rows'])

labels = read('quotient_label_result.json')
label_audit = read('quotient_label_audit.json')
assert labels['status'] == 'PASS_EXACT_N41_QUOTIENT_CODE_LABEL_SCREEN'
assert labels['degree_histogram']['2'] == 0 and labels['quotient_dimension'] == 17
assert label_audit['status'] == 'PASS_INDEPENDENT_N41_QUOTIENT_LABEL_DEGREE2_EXCLUSION'
assert label_audit['feature_rank'] == 37 and label_audit['augmented_ranks'] == [38] * 17
assert label_audit['producer_result_sha256'] == sha(HERE / 'quotient_label_result.json')

lean_output = (HERE / 'lean.stdout').read_text()
assert not (HERE / 'lean.stderr').read_bytes()
assert 'sorryAx' not in lean_output
assert all(f'AlignedSymmetry.{name}' in lean_output
           for name in ('ordered_pair', 'two_pair_swaps', 'pair_root_difference'))
assert 'depends on axioms' in lean_output
failure = read('preflight_failure.json')
assert failure['status'] == 'PREWORKLOAD_ENVIRONMENT_FAILURE'

terminal = {'status': 'PASS_ALIGNED_ROTATION_STAGE_REPLAY',
            'n41_relation_orientation': audit['orientation'],
            'n41_distinct_columns': audit['distinct_folded_columns'],
            'annihilator_dimensions': {'original': [1, 1], 'aligned': [17, 47]},
            'probe_rows': probe_counts,
            'n131_aligned_censored_rows': 1,
            'source_sha256': {name: sha(HERE / name) for name in
                              ('RESULT.md', 'n41_result.json', 'n41_audit_result.json',
                               'branch_rank_result.json', 'branch_rank_audit.json',
                               'build_n41_result.json', 'build_n41_ordered_result.json',
                               'build_n131_result.json', 'probe_n41_result.json',
                               'probe_n131_result.json', 'quotient_label_result.json',
                               'quotient_label_audit.json', 'lean.stdout')},
            'verifier_sha256': sha(Path(__file__))}
with (HERE / 'terminal_v2.json').open('x') as out:
    json.dump(terminal, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({key: terminal[key] for key in
                  ('status', 'n41_relation_orientation', 'n41_distinct_columns',
                   'annihilator_dimensions', 'probe_rows', 'n131_aligned_censored_rows')}))
