"""Relocation-aware terminal verifier for the W11 orbit SAT experiment."""
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=Path('/private/tmp/ecc2k130-w11-orbit-sat-20261019')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def data(name):return json.loads((HERE/name).read_text())
def transcript(name):
    p=HERE/name
    return p.read_bytes() if p.exists() else gzip.decompress((HERE/(name+'.gz')).read_bytes())
def verify_sources(name):
    protocol=data(name)
    for key,rec in protocol['sources'].items():
        p=Path(rec['path'])
        if p.is_relative_to(ORIGINAL):p=HERE/p.relative_to(ORIGINAL)
        assert sha(p)==rec['sha256'],(name,key)
    return protocol

build_protocol=verify_sources('orbit_build_protocol.json')
selector_protocol=verify_sources('selector_protocol.json')
query_protocol=verify_sources('orbit_query_protocol.json')
build=data('orbit_build_result.json')
selector=data('selector_result.json')
query=data('orbit_query_result.json')
assert build['status']=='PASS_W11_FOURPAIR_FULL_ASSIGNMENT'
assert build['source_codes']==[525,479,7,803] and build['orientation']==3
assert build['assignment_check']['clauses']==build['counts']['clauses']==40810
assert build['assignment_check']['xor_rows']==build['counts']['xor_rows']==2342
assert build['formula_sha256']==sha(HERE/'orbit41.xcnf')
assert build['protocol_sha256']==sha(HERE/'orbit_build_protocol.json')
with (HERE/'orbit41.xcnf').open() as inp:header=inp.readline().split()
assert header==['p','cnf',str(build['counts']['variables']),
                str(build['counts']['clauses']+build['counts']['xor_rows'])]
assert selector['status']=='PASS_ALL_64_ORBIT_SELECTOR_CODES'
assert (selector['valid_codes'],selector['excluded_codes'],selector['target_count'])==(41,23,41)
assert selector['formula_counts']==build['counts']
assert selector['protocol_sha256']==sha(HERE/'selector_protocol.json')
assert selector['script_sha256']==sha(HERE/'audit_selector.py')
assert query_protocol['worker_count']==1 and query_protocol['rss_cap_bytes']==4294967296
assert query['candidate_id'] is None and query['curve_id']==query_protocol['curve_id']
assert query['sampled_peak_combined_rss_bytes']<query_protocol['rss_cap_bytes']
assert query['wall_seconds']<=query_protocol['wall_cap_seconds']+1
raw=transcript('orbit_solver.stdout')
assert query['stdout_sha256']==hashlib.sha256(raw).hexdigest()
assert query['stderr_sha256']==sha(HERE/'orbit_solver.stderr')
assert query['protocol_sha256']==sha(HERE/'orbit_query_protocol.json')
if query['status']=='SAT_MODEL_PENDING_AUDIT':
    assert query['terminal_sat_line'] and b's SATISFIABLE' in raw
    audit_protocol=verify_sources('orbit_audit_protocol.json')
    audit=data('orbit_audit_result.json')
    assert audit['status']=='PASS_INDEPENDENT_N41_W11_ORBIT_SAT_PUBLIC_RELATION'
    assert audit['protocol_sha256']==sha(HERE/'orbit_audit_protocol.json')
    assert audit['distinct_folded_columns']==8
    assert audit['raw_group_sum_matches_target'] and audit['back_transport_matches_public_target']
    assert audit['projected_subgroup_sum_matches_target']
    final_status='PASS_SAT_GROUP_RELATION'
else:
    assert query['status'] in ('BOUNDED_UNKNOWN','WALL_CAP','RSS_CAP')
    assert not query['terminal_sat_line'] and not query['terminal_unsat_line']
    assert b's SATISFIABLE' not in raw and b's UNSATISFIABLE' not in raw
    final_status=query['status']
print(json.dumps({'status':'PASS_ARCHIVE_VERIFICATION','control':'PASS_FULL_ASSIGNMENT',
                  'selector':'PASS_ALL_64','query':final_status,'candidate_id':None},sort_keys=True))
