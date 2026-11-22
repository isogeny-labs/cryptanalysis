"""Terminal audit of the W33 exact-collision N131 public query."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE/name).read_text())


def pinned(name):
    p=HERE/name
    record=load(name)
    for source,digest in record['sources'].items():
        assert sha(source)==digest,(name,source)
    if 'script_sha256' in record:
        if name=='collision_protocol.json':script='collision_preflight.py'
        elif name=='filter_protocol.json':script='filter_valid_sage.py'
        elif name=='verify_protocol.json':script='verify_collision_sage.py'
        elif name=='sample_protocol.json':script='sample_validity_sage.py'
        elif name=='control_protocol.json':script='replay_model_sage.py'
        else:raise AssertionError(name)
        assert sha(HERE/script)==record['script_sha256']
    return record


for name in ('collision_protocol.json','filter_protocol.json','verify_protocol.json',
             'build_protocol.json','control_protocol.json','query_protocol.json',
             'sample_protocol.json'):
    pinned(name)
collision=load('collision_result.json')
filtered=load('filter_result.json')
verification=load('verification_result.json')
build=load('build_result.json')
control=load('control_replay.json')
query=load('query_result.json')
sample=load('sample_result.json')
qproto=load('query_protocol.json')
assert collision['status']=='EXACT_N131_W33_AFFINE_COLLISION_SPACES'
assert collision['case_count']==524
assert filtered['status']=='EXACT_VALID_N131_W33_FOLDED_COLLISION_PAIRS'
assert filtered['distinct_valid_collision_pairs']==8331
assert verification['status']=='PASS_INDEPENDENT_SAGE_ORBIT_AND_CURVE_VALIDITY_REPLAY'
assert verification['linear_cases_replayed']==524
assert verification['distinct_valid_collision_pairs']==8331
assert verification['valid_collision_occurrences']==16662
assert build['status']=='PASS_N131_W33_ALL_ALIGNED_COLLISION_EXACT_PUBLIC_CIRCUIT'
assert build['constructed_assignment_check']['clauses']==build['counts']['clauses']
assert build['constructed_assignment_check']['native_xor_rows']==build['counts']['xor_rows']
assert build['policy_counts']['collision_clauses']==83310
assert build['formula_sha256']==sha(HERE/'formula.xcnf')
assert build['input_wires_sha256']==sha(HERE/'input_wires.json')
assert control['status']=='PASS_W33_CONSTRUCTED_INDEPENDENT_GROUP_REPLAY'
assert len(set(control['folded_orbit_ids']))==10
assert query['status']=='BOUNDED_UNKNOWN' and query['stop_reason']=='WALL_CAP'
assert query['worker_count']==qproto['worker_count']==1
assert query['query_parent_wall_seconds']>=qproto['parent_wall_cap_seconds']
assert query['query_parent_wall_seconds']<qproto['parent_wall_cap_seconds']+1
assert query['sampled_peak_combined_rss_bytes']<qproto['rss_cap_bytes']
assert query['solver_stdout_sha256']==sha(HERE/'solver.stdout')
assert query['solver_stderr_sha256']==sha(HERE/'solver.stderr')
assert not query['solver_terminal_sat'] and not query['solver_terminal_unsat']
assert sample['status']=='PASS_N131_W29_W33_VALIDITY_SAMPLES'
assert [row['draws'] for row in sample['rows']]==[131072,131072]
assert sample['w29_exact_valid_codes']==67109836
assert (HERE/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.34.1'
assert sha(HERE/'FoldedCollision.lean')==sha(ROOT/'n131_w29_folded_collision_20261018/FoldedCollision.lean')
proof=(HERE/'lean.stdout').read_text()
assert proof.count('[propext, Classical.choice, Quot.sound]')==2
n41=json.loads((ROOT/'n41_n131_all_aligned_20261019/n41_audit_result.json').read_text())
assert n41['status']=='PASS_ALL_ALIGNED_N41_PUBLIC_RELATION'
assert n41['raw_group_sum_verified'] and n41['distinct_folded_columns']==10
assert collision['candidate_id'] is filtered['candidate_id'] is build['candidate_id'] is query['candidate_id'] is None
result={'status':'PASS_W33_EXPLORATORY_TERMINAL_AUDIT','candidate_id':None,
        'n41_control_sha256':sha(ROOT/'n41_n131_all_aligned_20261019/n41_audit_result.json'),
        'collision_result_sha256':sha(HERE/'collision_result.json'),
        'filter_result_sha256':sha(HERE/'filter_result.json'),
        'independent_collision_sha256':sha(HERE/'verification_result.json'),
        'group_control_sha256':sha(HERE/'control_replay.json'),
        'query_result_sha256':sha(HERE/'query_result.json'),
        'sample_result_sha256':sha(HERE/'sample_result.json'),
        'proof_output_sha256':sha(HERE/'lean.stdout'),
        'verifier_sha256':sha(__file__)}
(HERE/'terminal_audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result['status'])
