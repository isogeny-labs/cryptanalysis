"""Relocation-aware verifier of the complete W11 41-orientation census."""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ORIGINAL=Path('/private/tmp/ecc2k130-w11-fourpair-yield-20261019')
ORIGINAL_SAT=Path('/private/tmp/ecc2k130-w11-orbit-sat-20261019')
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929')
sys.path.insert(0,str(ROOT/'output_first_fifth_20261019'))
from output_first_math import FixedSeed
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def data(name):return json.loads((HERE/name).read_text())
def verify_sources(name):
    p=data(name)
    for key,rec in p['sources'].items():
        path=Path(rec['path'])
        if path.is_relative_to(ORIGINAL):path=HERE/path.relative_to(ORIGINAL)
        elif path.is_relative_to(ORIGINAL_SAT):
            path=path if HERE==ORIGINAL else PARENT/path.relative_to(ORIGINAL_SAT)
        assert sha(path)==rec['sha256'],(name,key)
    return p

query_protocol=verify_sources('query_protocol.json')
audit_protocol=verify_sources('audit_protocol.json')
query=data('query_result.json');audit=data('audit_result.json')
assert query['status']=='COMPLETE_CENSUS' and query['exit_code']==0
assert query['hit_lines']==32 and query['orientation_done_lines']==41
assert query['terminal_line'].split()[:6]==['TOTAL_HITS','41','32','51607520','32','0']
assert query['wall_seconds']<=600 and query['sampled_peak_combined_rss_bytes']<4294967296
assert query['stdout_sha256']==sha(HERE/'census.stdout')
assert query['stderr_sha256']==sha(HERE/'census.stderr')
assert query['protocol_sha256']==sha(HERE/'query_protocol.json')
assert audit['status']=='PASS_INDEPENDENT_N41_W11_ORBIT_CENSUS'
assert audit['hit_count']==32 and len(audit['orientation_counts'])==23
assert len(audit['witnesses'])==32
assert audit['protocol_sha256']==sha(HERE/'audit_protocol.json')
assert audit['script_sha256']==sha(HERE/'audit_sage.py')
assert audit_protocol['worker_count']==1

lines=(HERE/'census.stdout').read_text().splitlines()
hits=[line.split() for line in lines if line.startswith('HIT ')]
assert len(hits)==32 and sum(x.startswith('ORIENTATION_DONE ') for x in lines)==41
source=Path(query_protocol['sources']['join_input']['path']).read_text().splitlines()
assert source[0]=='W11FOUR 4 1124 1'
target=tuple(map(int,source[1].split()[2:]))
assert list(target)==audit['target']
states={}
for line in source[2:]:
    p=line.split()
    if p and p[0]=='S':states[(int(p[1]),int(p[2]))]=tuple(map(int,p[3:]))
fixed=FixedSeed(41,[0,3],56,11)
assert len(states)==4*1124
for index,line in enumerate(hits):
    orientation=int(line[1]);ids=[int(x) for x in line[2:6]]
    assert 0<=orientation<41
    assert audit['witnesses'][index]['orientation']==orientation
    assert audit['witnesses'][index]['state_ids']==ids
    P=None;cols=[];codes=[]
    for slot,sid in enumerate(ids):
        code,branch,a,b,ca,cb,x,y=states[(slot,sid)]
        assert fixed.source_a(code)==a and b==a^fixed.seed
        assert fixed.source_valid(a) and fixed.column(a)==ca and fixed.column(b)==cb
        assert (x,y) in fixed.pair_points(code,[0,12,24,36][slot])
        P=fixed.e.add(P,(x,y));cols.extend((ca,cb));codes.append(code)
    assert len(set(cols))==8 and P==fixed.e.frob(target,orientation)
    assert fixed.e.frob(P,(41-orientation)%41)==target
    assert audit['witnesses'][index]['source_codes']==codes
    assert audit['witnesses'][index]['folded_columns']==cols
print(json.dumps({'status':'PASS_ARCHIVE_VERIFICATION','hit_count':32,
    'orientations_with_hits':23,'candidate_id':None},sort_keys=True))
