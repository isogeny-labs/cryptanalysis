"""Recheck frozen W9 source, circuit, solver, proof, and join receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


fixture = load('fixture.json')
screen = load('screen_result.json')
assert screen['status'] == 'COMPLETE_CONSTRUCTED_CIRCUIT_SCREEN'
assert screen['curve_id'] == fixture['curve_id']
for row in screen['rows']:
    assert row['formula_sha256'] == sha(HERE / (row['variant'] + '.xcnf'))
    assert row['constructed_check']['clauses'] == row['counts']['clauses']
    assert row['constructed_check']['native_xor_rows'] == row['counts']['xor_rows']
assert {row['variant'] for row in screen['rows']} == {'exact5', 'exact3', 'table5'}
assert load('census_result.json')['status'] == 'PASS_EXHAUSTIVE_W9_SOURCE_GATE_TABLE_EQUIVALENCE'
sage_census = load('census_sage_result.json')
assert sage_census['status'] == 'PASS_INDEPENDENT_SAGE_W9_SOURCE_CENSUS'
assert len(sage_census['accepted_masks']) == 71
assert load('control_audit_result.json')['status'] == 'PASS_INDEPENDENT_W9_CONSTRUCTED_CONTROL'
for variant in ('exact3', 'table5'):
    query = load(variant + '_result.json')
    assert query['status'] == 'BOUNDED_UNKNOWN'
    assert len(query['attempts']) == 1 and not query['cuts']
    assert query['attempts'][0]['stop_reason'] == 'TIME_CAP'
    assert query['attempts'][0]['formula_sha256'] == sha(HERE / (variant + '.xcnf'))
    assert query['attempts'][0]['solver_stdout_sha256'] == sha(HERE / (variant + '_attempt0.stdout'))
    assert query['attempts'][0]['solver_stderr_sha256'] == sha(HERE / (variant + '_attempt0.stderr'))
    assert query['protocol_sha256'] == sha(HERE / (variant + '_protocol.json'))
probe = load('probe_result.json')
assert probe['status'] == 'COMPLETE_EXPLORATORY_FIXED_CONFLICT_PROBE'
assert probe['protocol_sha256'] == sha(HERE / 'probe_protocol.json')
assert [row['variant'] for row in probe['rows']] == ['exact5', 'exact3', 'table5']
assert all(row['status_lines'] == ['s INDETERMINATE'] and row['last_restart']
           for row in probe['rows'])
control = load('join_sage_control_result.json')
assert control['status'] == 'PASS_CHECKED_SAGE_TARGET_CONDITIONED_W9_CONTROL'
assert control['orientation'] == 3 and control['states_per_slot'] == 8
assert load('host_sample_retry1.json')['host_cpu_percent_over_one_second'] >= 90
diagnostic = load('launch_diagnostic.json')
assert all(row['status'] == 'EXITED' and row['returncode'] == 2
           for row in diagnostic['rows'])
assert (HERE / 'target_join.stdout').read_bytes() == b''
assert (HERE / 'target_join.stderr').read_bytes() == b''
lean_stdout = (HERE / 'lean.stdout').read_text()
assert not (HERE / 'lean.stderr').read_bytes()
assert 'error:' not in lean_stdout and 'sorryAx' not in lean_stdout
for theorem in ('invalid_code_cut', 'collision_cut', 'two_one_two_lookup'):
    assert "'LazySourceCuts." + theorem + "'" in lean_stdout
assert 'depends on axioms: [propext, Classical.choice, Quot.sound]' in lean_stdout
assert 'two_one_two_lookup\' does not depend on any axioms' in lean_stdout
assert 'sorry' not in (HERE / 'LazySourceCuts.lean').read_text()

retry = load('target_join_result_retry1.json')
assert retry['protocol_sha256'] == sha(HERE / 'target_join_protocol_retry1.json')
assert retry['stdout_sha256'] == sha(HERE / 'target_join_retry1.stdout')
assert retry['stderr_sha256'] == sha(HERE / 'target_join_retry1.stderr')
assert retry['left_done'] and retry['right_done']
assert retry['left_done'][0].split()[1] == '79424'
assert retry['right_done'][0].split()[1] == '79424'
if retry['status'] == 'HIT_PENDING_SAGE_REPLAY':
    audit = load('target_join_audit_result_retry1.json')
    assert audit['status'] == 'PASS_INDEPENDENT_TARGET_CONDITIONED_N41_PUBLIC_RELATION'
    assert audit['distinct_folded_columns'] == 10
    assert audit['raw_public_point'] == fixture['original_raw_point']
    assert audit['subgroup_public_point'] == fixture['original_subgroup_point']
elif retry['status'] == 'BOUNDED_UNKNOWN':
    assert retry['stop_reason'] in ('PARENT_WALL_CAP', 'RSS_CAP')
else:
    raise AssertionError(retry['status'])

sample = json.loads((PRIOR / 'sample_result.json').read_text())['sample']
assert sample['samples'] == 65536 and sample['usable_sample_edges'] == 16677
projection = sample['usable_sample_edges'] * (1 << 28) // sample['samples']
assert projection == 68308992
r = 680564733841876926932320129493409985129
lo, hi = 0, 1 << 27
while lo + 1 < hi:
    middle = (lo + hi) // 2
    if middle**5 >= r:
        hi = middle
    else:
        lo = middle
assert hi == 58421660
manifest = {path.name: sha(path) for path in sorted(HERE.iterdir())
            if path.is_file() and path.name != 'verification.json'}
result = {'status': 'PASS_W9_EVIDENCE_CHECK', 'candidate_id': None,
          'curve_id': fixture['curve_id'], 'native_retry_status': retry['status'],
          'n131_usable_edge_projection': projection,
          'optimistic_equal_list_threshold': hi,
          'optimistic_pair_entries': hi * hi,
          'source_sha256': manifest}
with (HERE / 'verification.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'native_retry_status': retry['status'],
                  'artifact_count': len(manifest)}))
