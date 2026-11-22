"""Read-only terminal audit of the N41 shared-inverse and exact-join receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda name:json.loads((HERE/name).read_text())
sat_protocol=read('protocol.json')
join_protocol=read('join_protocol.json')
for record in (sat_protocol,join_protocol):
    for path,digest in record['sources'].items():assert sha(path)==digest,path
build=read('build_result.json')
base=read('two_inverse_build_result.json')
base_check=read('two_inverse_check_result.json')
sat=read('public_result.json')
join=read('join_result.json')
audit=read('join_audit_result.json')
control=read('audit_result.json')
assert sat['protocol_sha256']==sha(HERE/'protocol.json')
assert join['protocol_sha256']==audit['join_protocol_sha256']==sha(HERE/'join_protocol.json')
assert audit['join_result_sha256']==sha(HERE/'join_result.json')
assert sha(HERE/'solver.stdout')==sat['sha256']['solver.stdout']
assert sha(HERE/'solver.stderr')==sat['sha256']['solver.stderr']
assert sha(HERE/'join.stdout.txt')==join['stdout_sha256']
assert sha(HERE/'join.stderr.txt')==join['stderr_sha256']
assert build['panels'][1]['xcnf_sha256']==sha(HERE/'public.xcnf')
assert build['panels'][0]['xcnf_sha256']==sha(HERE/'control.xcnf')
assert build['panels'][0]['control_check']=={'clauses':82957,'native_xor_rows':3692}
assert base_check['status']=='PASS_MATCHED_SIXPAIR_TWO_INVERSE_CONTROL'
assert base['and_gates']-build['panels'][1]['and_gates']==1722
assert sat['status']=='BOUNDED_UNKNOWN' and sat['stop_reason']=='PARENT_WALL_CAP'
assert join['status']=='HIT_PENDING_SAGE_REPLAY' and not join['stop_reason']
assert audit['status']=='PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
assert control['status']=='PASS_INDEPENDENT_N41_SIXPAIR_REPLAY'
assert audit['distinct_columns']==12 and len(audit['pair_rows'])==6
assert audit['subgroup_target']==sat_protocol['public_subgroup_point']
assert not (HERE/'lean_check_final_verified.stderr.txt').read_text()
lean=(HERE/'lean_check_final_verified.stdout.txt').read_text()
assert lean.count('does not depend on any axioms')==2
receipt={'status':'PASS_N41_SIXPAIR_TERMINAL_AUDIT','candidate_id':None,
         'verified_relation_point':audit['subgroup_target'],
         'join_wall_ns':join['wall_ns'],'join_peak_rss_bytes':join['sampled_peak_combined_rss_bytes'],
         'sat_status':sat['status'],'sat_wall_ns':sat['wall_ns'],
         'and_gate_saving':1722,
         'sha256':{name:sha(HERE/name) for name in (
             'protocol.json','join_protocol.json','build_result.json','two_inverse_build_result.json',
             'two_inverse_check_result.json','audit_result.json','public_result.json','join_result.json',
             'join_audit_result.json','SixPairJoin.lean','lean_check_final_verified.stdout.txt')}}
with (HERE/'terminal.json').open('x') as out:json.dump(receipt,out,sort_keys=True,indent=2);out.write('\n')
print(receipt['status'])
