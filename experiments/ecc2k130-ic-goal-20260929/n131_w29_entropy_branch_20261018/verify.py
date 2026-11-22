"""Read-only reconstruction of the frozen N131 prefix arm and receipts."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


cfg = read('protocol.json')
result = read('result.json')
mapping_cfg = read('mapping_audit_protocol.json')
mapping = read('mapping_audit_result.json')
prefix_cfg = read('prefix_protocol.json')
prefix = read('prefix_result.json')
prefix_audit_cfg = read('prefix_audit_protocol.json')
prefix_audit = read('prefix_audit_result.json')
startup_failure = read('attempt1_runtime_failure.json')
for name, source in cfg['sources'].items():
    assert sha(source['path']) == source['sha256'], name
for name, source in mapping_cfg['sources'].items():
    assert sha(source['path']) == source['sha256'], name
assert mapping['status'] == 'PASS_EXACT_3P2_FORMULA_AND_MASK_WIRE_REBUILD'
assert mapping['audit_protocol_sha256'] == sha(HERE / 'mapping_audit_protocol.json')
assert mapping['auditor_sha256'] == sha(HERE / 'audit_mapping_sage.py')
assert mapping['first_mask_bits'] == list(range(8))
assert mapping['first_mask_variables'] == list(range(1, 9))
assert mapping['original_formula_sha256'] == cfg['sources']['original_xcnf']['sha256']
for source_cfg in (prefix_cfg, prefix_audit_cfg):
    for name, source in source_cfg['sources'].items():
        assert sha(source['path']) == source['sha256'], name
assert prefix['status'] == prefix['native']['status'] == 'COMPLETE_PREFIX_CENSUS'
assert prefix['protocol_sha256'] == sha(HERE / 'prefix_protocol.json')
assert prefix['stdout_sha256'] == sha(HERE / 'prefix.stdout')
assert prefix['stderr_sha256'] == sha(HERE / 'prefix.stderr')
assert prefix['exit_code'] == 0 and prefix['stop_reason'] is None
assert prefix['sampled_peak_combined_rss_bytes'] < prefix_cfg['combined_rss_cap_bytes']
assert prefix['parent_wall_seconds'] < prefix_cfg['parent_wall_cap_seconds']
assert prefix['native']['canonical_masks'] == 1 << 20
assert prefix['native']['inverse_checks'] == 1 << 21
assert prefix_audit['status'] == 'COMPLETE_INDEPENDENT_SAGE_PREFIX_CENSUS'
assert startup_failure['status'] == 'STARTUP_STORAGE_FAILURE'
assert startup_failure['solver_started'] is False
assert startup_failure['retry_runtime_info_sha256'] == sha(HERE / 'sage_runtime_info.json')
assert prefix_audit['canonical_masks_checked'] == 1 << 20
assert prefix_audit['audit_protocol_sha256'] == sha(HERE / 'prefix_audit_protocol.json')
assert prefix_audit['auditor_sha256'] == sha(HERE / 'audit_prefix_sage.py')
for field in ('eligible_edges', 'left_inverse_trace_zero',
              'right_inverse_trace_zero', 'first_eligible', 'last_eligible'):
    assert prefix_audit[field] == prefix['native'][field]
assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
assert cfg['candidate_id'] is None and result['candidate_id'] is None
assert cfg['curve_id'] == result['curve_id']
assert cfg['workload_id'] == result['workload_id']
assert cfg['mask_bit_positions'] == list(range(8))
assert cfg['mask_variable_ids'] == list(range(1, 9))
assert cfg['branch_prefix_value'] == result['branch_prefix_value'] == 3
assert result['formula_bytes'] > 7_000_000
assert result['rss_samples'] > 0
assert result['sampled_peak_combined_rss_bytes'] <= cfg['combined_rss_cap_bytes']
assert result['parent_wall_seconds'] <= cfg['parent_wall_cap_seconds'] + 1

# Reconstruct the exact XCNF hash from the immutable original and eight units.
original = Path(cfg['sources']['original_xcnf']['path'])
h = hashlib.sha256()
size = 0
with original.open('rb') as source:
    header = source.readline()
    assert header == b'p cnf 121204 274931\n'
    generated = b'p cnf 121204 274939\n'
    h.update(generated)
    size += len(generated)
    for i, variable in enumerate(cfg['mask_variable_ids']):
        lit = variable if cfg['branch_prefix_value'] >> i & 1 else -variable
        generated = f'{lit} 0\n'.encode()
        h.update(generated)
        size += len(generated)
    for block in iter(lambda: source.read(1 << 20), b''):
        h.update(block)
        size += len(block)
assert h.hexdigest() == result['formula_sha256']
assert size == result['formula_bytes']

for stream in ('stdout', 'stderr'):
    path = HERE / f'solver.{stream}.gz'
    assert sha(path) == result[f'compressed_{stream}_sha256']
    raw = gzip.open(path, 'rb').read()
    assert hashlib.sha256(raw).hexdigest() == result[f'raw_{stream}_sha256']
stdout = gzip.open(HERE / 'solver.stdout.gz', 'rt', errors='replace').read()
statuses = [line for line in stdout.splitlines() if line.startswith('s ')]
assert statuses == result['status_lines']
assert result['model_line_count'] == sum(line.startswith('v ') for line in stdout.splitlines())
assert result['restart_rows'] == sum(line.startswith('c rst') for line in stdout.splitlines())
if result['status'] == 'SAT_PENDING_INDEPENDENT_GROUP_REPLAY':
    assert 's SATISFIABLE' in statuses and result['model_line_count'] > 0
elif result['status'] == 'BOUNDED_UNKNOWN':
    assert 's SATISFIABLE' not in statuses and 's UNSATISFIABLE' not in statuses
print('REPLAY_PASS: sources, exact branched XCNF, cap receipt, compressed solver logs')
