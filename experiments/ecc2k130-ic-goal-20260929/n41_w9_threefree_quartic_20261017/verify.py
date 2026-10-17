"""Check frozen inputs and independent three-free-slot result agreement."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


bindings = [
    ('protocol.json', 'result.json', {
        'script': HERE / 'search_sage.py',
        'runtime': HERE / 'sage_runtime_info.json',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'prior': ROOT / 'n41_w9_two_product_eliminant_20261017/result.json',
    }),
    ('group_audit_protocol.json', 'group_audit_result.json', {
        'script': HERE / 'audit_group_index_sage.py',
        'runtime': HERE / 'group_audit_runtime_info.json',
        'states': ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json',
        'producer': HERE / 'result.json',
    }),
]
for protocol_name, result_name, sources in bindings:
    protocol = read(protocol_name)
    result = read(result_name)
    assert result['protocol_sha256'] == sha(HERE / protocol_name)
    assert all(protocol['source_sha256'][k] == sha(path)
               for k, path in sources.items())
    assert result['status'].startswith('PASS_')

producer = read('result.json')
group = read('group_audit_result.json')
assert producer['candidate_id'] is None
assert producer['specialized_quartic_queries'] == 284 * 71
assert producer['exceptional_outer_states'] == []
assert producer['algebraic_code_hits'] == [[244, 11, 16], [244, 16, 11]]
assert producer['gcd_degree_total'] == 2
assert group['pair_signed_assignments_indexed'] == 284**2
assert group['outer_signed_states_queried'] == 284
assert group['raw_group_hits'] == 2
assert sorted(producer['exact_witnesses']) == group['exact_witnesses']
assert group['exact_witnesses'] == [[105, 244, 47, 66, 111],
                                    [105, 244, 66, 47, 111]]
assert not (HERE / 'run.stderr').read_text()
assert not (HERE / 'group_audit.stderr').read_text()
print(json.dumps({'status': 'PASS_THREEFREE_TERMINAL_BINDINGS',
                  'quartic_queries': producer['specialized_quartic_queries'],
                  'group_pairs': group['pair_signed_assignments_indexed'],
                  'witnesses': group['exact_witnesses']}))
