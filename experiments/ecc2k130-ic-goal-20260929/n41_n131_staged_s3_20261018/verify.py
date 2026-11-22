"""Replay frozen staged-S3 audit, controls, solver arms and query receipt."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ('audit_protocol.json','build_protocol.json','probe_protocol.json',
             'ordered_build_protocol.json','ordered_probe_protocol.json',
             'query_protocol.json'):
    p=json.loads((here/name).read_text())
    for path,digest in p['sources'].items():
        assert sha(path)==digest,(name,path)
audit=json.loads((here/'audit_result.json').read_text())
assert audit['status']=='PASS_FIRST_TWO_PAIR_EXCEPTION_AUDIT'
assert audit['protocol_sha256']==sha(here/'audit_protocol.json')
assert audit['n41']['disjoint_ordered_pairs']==79424
assert audit['n41']['identity_sums']==audit['n41']['zero_x_sums']==0
assert audit['n131_sample']['source_codes']==512
assert audit['n131_sample']['cross_code_equal_x_candidates']==0
assert audit['n131_sample']['cross_code_product_one_candidates']==0
stage=json.loads((here/'build_result.json').read_text())
ordered=json.loads((here/'ordered_build_result.json').read_text())
assert stage['status']=='PASS_N41_STAGED_S3_CIRCUIT'
assert ordered['status']=='PASS_N41_STAGED_S3_ORDERED_CIRCUIT'
assert stage['formula_sha256']==sha(here/'formula.xcnf')
assert ordered['formula_sha256']==sha(here/'ordered_formula.xcnf')
assert stage['protocol_sha256']==sha(here/'build_protocol.json')
assert ordered['protocol_sha256']==sha(here/'ordered_build_protocol.json')
assert len(stage['controls_checked'])==33
assert sum(row['preceding_zero'] for row in stage['controls_checked'])==1
assert all(row['source_zero'] and row['first_s3_zero'] and
           row['second_s3_zero'] and row['pair_zero'] and row['s3_zero']
           for row in stage['controls_checked'])
assert ordered['exhaustive_code_pairs_checked']==65536
assert ordered['comparator_gates']==30 and ordered['comparator_clauses']==149
for filename,arms_expected in [('probe_result.json',['quadratic','staged','staged','quadratic']),
                               ('ordered_probe_result.json',['quadratic','ordered_staged','ordered_staged','quadratic'])]:
    probe=json.loads((here/filename).read_text())
    assert probe['status']=='COMPLETED_FROZEN_ABBA_PROBE'
    protocol='ordered_probe_protocol.json' if filename.startswith('ordered') else 'probe_protocol.json'
    assert probe['protocol_sha256']==sha(here/protocol)
    arms=probe['arm_results']
    assert [row['arm'] for row in arms]==arms_expected
    assert all(row['status']=='INDETERMINATE_CONFLICT_CAP' and
               row['monitor_error'] is None and row['reported_conflicts']>=20000
               for row in arms)
    if filename.startswith('ordered'):
        for i,j in ((1,0),(2,3)):
            assert arms[i]['reported_decisions']<=.9*arms[j]['reported_decisions']
            assert arms[i]['wall_seconds']<=.75*arms[j]['wall_seconds']
            print('ordered_staged_pair',i,j,
                  'decisions',arms[i]['reported_decisions']/arms[j]['reported_decisions'],
                  'wall',arms[i]['wall_seconds']/arms[j]['wall_seconds'])
lean=(here/'lean_check.log').read_text()
assert (here/'lean_exit_code.txt').read_text().strip()=='0'
assert "'StagedS3.staged_s3_implies_f4' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert not any(word in (here/'StagedS3.lean').read_text()
               for word in ('sorry','admit','sorryAx'))
query=json.loads((here/'query_result.json').read_text())
assert query['protocol_sha256']==sha(here/'query_protocol.json')
assert query['solver_stdout_sha256']==sha(here/'solver.stdout')
assert query['solver_stderr_sha256']==sha(here/'solver.stderr')
assert query['worker_count']==1 and query['monitor_error'] is None
assert query['sampled_peak_combined_rss_bytes']<=4294967296
assert query['status'] in ('BOUNDED_UNKNOWN','SAT_MODEL_UNVERIFIED')
if query['status']=='SAT_MODEL_UNVERIFIED':
    replay=json.loads((here/'replay_result.json').read_text())
    assert replay['status']=='PASS_INDEPENDENT_SAGE_MODEL_GROUP_REPLAY'
    assert replay['independent_group_matches']>0
print('PASS_STAGED_S3_EVIDENCE_REPLAY',query['status'])
