"""Relocation-aware terminal verifier for the W10 four-pair SAT experiment."""
import hashlib
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=Path('/private/tmp/ecc2k130-w10-orbit-sat-20261019')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def data(name):return json.loads((HERE/name).read_text())
def transcript(name):
    path=HERE/name
    if path.exists():return path.read_bytes()
    return gzip.decompress((HERE/(name+'.gz')).read_bytes())
def verify_sources(name):
    p=data(name)
    for key,rec in p['sources'].items():
        path=Path(rec['path'])
        if path.is_relative_to(ORIGINAL):path=HERE/path.relative_to(ORIGINAL)
        assert sha(path)==rec['sha256'],(name,key)
    return p

build_protocol=verify_sources('build_protocol.json')
orbit_build_protocol=verify_sources('orbit_build_protocol.json')
query_protocol=verify_sources('query_protocol.json')
orbit_query_protocol=verify_sources('orbit_query_protocol.json')
selector_protocol=verify_sources('selector_protocol.json')
selector_v2_protocol=verify_sources('selector_v2_protocol.json')
build=data('build_result.json');orbit_build=data('orbit_build_result.json')
query=data('query_result.json');orbit_query=data('orbit_query_result.json')
selector=data('selector_v2_result.json')

for stem,protocol,result,formula in [
        ('fixed',build_protocol,build,'orientation29.xcnf'),
        ('orbit',orbit_build_protocol,orbit_build,'orbit41.xcnf')]:
    assert result['status']=='PASS_W10_FOURPAIR_FULL_ASSIGNMENT'
    assert result['assignment_check']['clauses']==result['counts']['clauses']
    assert result['assignment_check']['xor_rows']==result['counts']['xor_rows']
    assert result['formula_sha256']==sha(HERE/formula)
    assert result['protocol_sha256']==sha(HERE/('build_protocol.json' if stem=='fixed' else 'orbit_build_protocol.json'))
    with (HERE/formula).open() as inp:header=inp.readline().split()
    assert header==['p','cnf',str(result['counts']['variables']),
                    str(result['counts']['clauses']+result['counts']['xor_rows'])]
    assert protocol['worker_count']==1 and protocol['rss_cap_bytes']==4294967296

assert selector['status']=='PASS_ALL_64_ORBIT_SELECTOR_CODES'
assert (selector['valid_codes'],selector['excluded_codes'],selector['target_count'])==(41,23,41)
assert selector['formula_counts']==orbit_build['counts']
assert selector['protocol_sha256']==sha(HERE/'selector_v2_protocol.json')
assert selector['script_sha256']==sha(HERE/'audit_selector_v2.py')
assert selector_v2_protocol['sources']['attempt1_stderr']['sha256']==sha(HERE/'selector_attempt1.stderr')
assert 'AssertionError' in (HERE/'selector_attempt1.stderr').read_text()

for protocol,result,out,err,status in [
        (query_protocol,query,'solver.stdout','solver.stderr','BOUNDED_UNKNOWN'),
        (orbit_query_protocol,orbit_query,'orbit_solver.stdout','orbit_solver.stderr','WALL_CAP')]:
    assert result['status']==status
    assert result['candidate_id'] is None and result['curve_id']==protocol['curve_id']
    assert protocol['worker_count']==1 and protocol['rss_cap_bytes']==4294967296
    assert result['sampled_peak_combined_rss_bytes']<protocol['rss_cap_bytes']
    assert result['wall_seconds']<=protocol['wall_cap_seconds']+1
    raw=transcript(out)
    assert result['stdout_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['stderr_sha256']==sha(HERE/err)
    assert not result['terminal_sat_line'] and not result['terminal_unsat_line']
    assert b's SATISFIABLE' not in raw
    assert b's UNSATISFIABLE' not in raw
    assert result['protocol_sha256']==sha(HERE/('query_protocol.json' if status=='BOUNDED_UNKNOWN' else 'orbit_query_protocol.json'))
assert orbit_query['stop_reason']=='WALL_CAP' and orbit_query['exit_code']==-15
assert query['stop_reason'] is None and query['exit_code']==0

print(json.dumps({'status':'PASS_ARCHIVE_VERIFICATION','control':'PASS_FULL_ASSIGNMENT',
    'selector':'PASS_ALL_64','fixed_query':query['status'],
    'orbit_query':orbit_query['status'],'candidate_id':None},sort_keys=True))
