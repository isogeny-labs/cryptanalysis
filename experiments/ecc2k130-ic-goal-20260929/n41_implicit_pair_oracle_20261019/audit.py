"""Audit frozen pair-oracle inputs, statuses, proof, and exact control labels."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


protocol_names = ('key_protocol.json', 'build_protocol.json',
                  'query_protocol.json', 'table_build_protocol.json',
                  'table_query_protocol.json', 'scan_protocol.json')
source_count = 0
for name in protocol_names:
    protocol = read(name)
    assert protocol['candidate_id'] is None
    for path, expected in protocol['sources'].items():
        assert sha(path) == expected, (name, path)
        source_count += 1
keys = read('keys.json')
build = read('build_result.json')
query = read('query_result.json')
table_build = read('table_build_result.json')
table_query = read('table_query_result.json')
scan = read('scan_result.json')
assert keys['status'] == 'PASS_N41_TWO_PAIR_KEY_CENSUS'
assert keys['left_entries'] == keys['distinct_left_keys'] == 79424
assert len(keys['keys']) == 8
assert build['status'] == 'PASS_N41_TWO_PAIR_ORACLE_BUILD'
assert table_build['status'] == 'PASS_N41_TWO_PAIR_TABLE_ABLATION_BUILD'
assert len(build['rows']) == len(query['rows']) == 8
assert len(table_build['rows']) == len(table_query['rows']) == 2
assert scan['status'] == 'PASS_N41_TWO_PAIR_IMPLICIT_SPAN_ORACLE_PANEL'
assert scan['product_basis_rank'] == 8 and len(scan['rows']) == 8
assert scan['keys_sha256'] == sha(HERE / 'keys.json')
assert all(row['status'] == 'BOUNDED_UNKNOWN' and row['stop_reason'] == 'WALL_CAP'
           for row in query['rows'] + table_query['rows'])
for panel, suffix in ((query, ''), (table_query, '_table')):
    for row in panel['rows']:
        assert row['stdout_sha256'] == sha(HERE / f"{row['key_id']}{suffix}.stdout")
        assert row['stderr_sha256'] == sha(HERE / f"{row['key_id']}{suffix}.stderr")
for key, row in zip(keys['keys'], scan['rows']):
    assert key['key_id'] == row['key_id']
    assert key['exact_member'] == row['exact_member'] == row['oracle_member']
    assert row['counts']['left_scanned'] == 284
    assert row['counts']['column_compatible_hits'] == len(row['witnesses'])
    if key['exact_member']:
        assert row['counts']['product_span_hits'] >= 1 and row['witnesses']
    else:
        assert not row['witnesses']
for row in build['rows'] + table_build['rows']:
    suffix = '_table' if row in table_build['rows'] else ''
    assert row['formula_sha256'] == sha(HERE / f"{row['key_id']}{suffix}.xcnf")
    if row['exact_member']:
        assert row['constructed_witness_check'] == {
            'clauses': row['counts']['clauses'],
            'native_xor_rows': row['counts']['xor_rows']}
lean = (HERE / 'lean.stdout').read_text()
for theorem in ('recover_product', 'reject_outside_span'):
    assert f"'SourceProductRecovery.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert not (HERE / 'lean.stderr').read_text()
assert re.search(r'\b(?:sorry|admit|sorryAx)\b',
                 (HERE / 'SourceProductRecovery.lean').read_text()) is None
result = {'status': 'PASS_N41_IMPLICIT_PAIR_ORACLE_TERMINAL_AUDIT',
          'candidate_id': None, 'protocols_verified': len(protocol_names),
          'source_hashes_verified': source_count, 'keys_verified': 8,
          'sat_bounded_rows': len(query['rows']) + len(table_query['rows']),
          'scan_exact_agreements': len(scan['rows']),
          'script_sha256': sha(__file__)}
(HERE / 'terminal_audit.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
