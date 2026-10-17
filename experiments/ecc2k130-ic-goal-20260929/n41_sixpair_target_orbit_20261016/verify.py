"""Terminal hash, status, group, assignment, and proof audit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda name:json.loads((HERE/name).read_text())
for name in ('protocol.json','join_protocol.json','audit_protocol.json','assignment_protocol.json','closure_protocol.json'):
    record=read(name)
    for path,digest in record['sources'].items():assert sha(path)==digest,path
build=read('build_result.json');sat=read('public_result.json')
orbit=read('orbit_audit.json');join=read('join_result.json')
audit=read('join_audit.json');assign=read('assignment_audit.json')
closure=read('closure_audit.json')
assert sat['protocol_sha256']==sha(HERE/'protocol.json')
assert join['protocol_sha256']==sha(HERE/'join_protocol.json')
assert sat['sha256']['solver.stdout']==sha(HERE/'solver.stdout')
assert sat['sha256']['solver.stderr']==sha(HERE/'solver.stderr')
assert join['stdout_sha256']==sha(HERE/'join.stdout')
assert join['stderr_sha256']==sha(HERE/'join.stderr')
assert build['panels'][1]['xcnf_sha256']==sha(HERE/'public.xcnf')
assert build['panels'][0]['xcnf_sha256']==sha(HERE/'control.xcnf')
assert build['panels'][0]['control_check']=={
    'clauses':88698,'native_xor_rows':3826}
assert sat['status']=='BOUNDED_UNKNOWN' and sat['stop_reason']=='PARENT_WALL_CAP'
assert not sat['monitor_degraded'] and not sat['terminal_lines']
assert sum(line.startswith('c rst ') for line in (HERE/'solver.stdout').read_text(errors='replace').splitlines())==3006
assert orbit['status']=='PASS_N41_FROBENIUS_TARGET_ORBIT' and orbit['raw_orbit_size']==41
assert closure['status']=='PASS_N41_SIGNED_FROBENIUS_CLOSURE'
assert closure['actual_usable_projected_points_B']==6314
assert join['status']=='COMPLETE' and join['orbits_completed']==41
assert len(join['hits'])==41 and join['terminal'][0].startswith('CENSUS_COMPLETE 41 ')
assert audit['status']=='PASS_N41_41_ORBIT_GROUP_AND_ROW_AUDIT'
assert audit['relation_count']==audit['final_rank']==41 and audit['rank_prefix']==list(range(1,42))
assert assign['status']=='PASS_41_PUBLIC_ORBIT_XCNF_ASSIGNMENTS'
assert assign['count']==41 and assign['clauses']==88698 and assign['native_xor_rows']==3826
assert not (HERE/'lean.stderr').read_text()
assert "'SixPairTargetOrbit.relation_pullback' depends on axioms: [propext, Quot.sound]" in (HERE/'lean.stdout').read_text()
out={'status':'PASS_N41_SIXPAIR_41_ORBIT_TERMINAL_AUDIT','candidate_id':None,
     'sat_status':sat['status'],'exact_join_orbit_hits':41,'independent_rank':41,
     'sha256':{name:sha(HERE/name) for name in ('protocol.json','build_result.json',
         'public_result.json','orbit_audit.json','join_protocol.json','join_result.json',
         'audit_protocol.json','join_audit.json','assignment_protocol.json',
         'assignment_audit.json','closure_protocol.json','closure_audit.json',
         'OrbitTransport.lean','lean.stdout')}}
(HERE/'terminal.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(out['status'])
