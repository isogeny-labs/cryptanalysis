"""Relocation-aware, independent terminal check of the frozen N41 record."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/private/tmp/ecc2k130-w34-fourpair-20261019')
MATH = Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019/output_first_math.py')
sys.path.insert(0, str(MATH.parent))
from output_first_math import FixedSeed

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

checks = {}
for name in ('prepare_protocol.json', 'query_protocol.json', 'audit_v3_protocol.json',
             'n131_density_protocol.json', 'base_audit_protocol.json',
             'w10/prepare_protocol.json', 'w10/query_protocol.json',
             'w10/audit_protocol.json', 'w9/prepare_protocol.json',
             'w9/query_protocol.json'):
    protocol = json.loads((HERE/name).read_text())
    for key, rec in protocol.get('sources', {}).items():
        if not isinstance(rec, dict) or 'path' not in rec:
            continue
        p = Path(rec['path'])
        if p.is_relative_to(ORIGINAL):
            p = HERE/p.relative_to(ORIGINAL)
        assert sha(p) == rec['sha256'], (name, key)
        checks[f'{name}:{key}'] = True
    if name == 'n131_density_protocol.json':
        assert sha(MATH) == protocol['source_sha256']
        assert sha(HERE/'n131_density.py') == protocol['script_sha256']

prepare = json.loads((HERE/'prepare_result.json').read_text())
query = json.loads((HERE/'query_result.json').read_text())
audit = json.loads((HERE/'audit_result.json').read_text())
density = json.loads((HERE/'n131_density_result.json').read_text())
assert prepare['input_sha256'] == sha(HERE/'join4_input.tsv')
assert query['stdout_sha256'] == sha(HERE/'join4.stdout')
assert query['stderr_sha256'] == sha(HERE/'join4.stderr')
assert query['status'] == 'COMPLETE_HIT' and query['exit_code'] == 0
assert query['wall_seconds'] <= 600 and query['sampled_peak_combined_rss_bytes'] < 4294967296
assert audit['status'] == 'PASS_INDEPENDENT_N41_W11_FOURPAIR_PUBLIC_RELATION'
assert audit['protocol_sha256'] == sha(HERE/'audit_v3_protocol.json')
assert audit['distinct_folded_columns'] == 8
assert audit['raw_group_sum_matches_target'] and audit['back_transport_matches_public_target']
assert audit['projected_subgroup_sum_matches_target']
assert density['status'] == 'COMPLETE_N131_DENSITY_DIAGNOSTIC'
assert density['protocol_sha256'] == sha(HERE/'n131_density_protocol.json')
assert density['script_sha256'] == sha(HERE/'n131_density.py')
assert [(r['width'],r['sample_size']) for r in density['rows']] == [(33,8192),(34,8192)]

hit = query['terminal_line'].split()
assert hit[0] == 'HIT'
orientation = int(hit[1])
state_ids = [int(x) for x in hit[2:6]]
assert orientation == audit['orientation'] and state_ids == [row['state_id'] for row in audit['rows']]
fixed = FixedSeed(41, [0,3], 56, 11)
source_lines = (HERE/'join4_input.tsv').read_text().splitlines()
assert source_lines[0] == 'W11FOUR 4 1124 1'
target_line = source_lines[1].split()
assert target_line[:2] == ['T','0']
target = tuple(map(int,target_line[2:]))
assert list(target) == audit['raw_target_point']
states = {}
for line in source_lines[2:]:
    p = line.split()
    if p[0] == 'S':
        slot,sid,code,branch,a,b,ca,cb,x,y = map(int,p[1:])
        states[(slot,sid)] = (code,branch,a,b,ca,cb,x,y)
assert len(states) == 4*1124
sum_point = None
all_columns = set()
for slot,sid in enumerate(state_ids):
    code,branch,a,b,ca,cb,x,y = states[(slot,sid)]
    row = audit['rows'][slot]
    assert code == row['source_code']
    assert [a,b] == row['source_masks'] and [ca,cb] == row['folded_columns']
    assert fixed.source_valid(a) and fixed.source_product(code) == fixed.f.mul(a,b)
    assert fixed.column(a) == ca and fixed.column(b) == cb
    assert fixed.e.on_curve((x,y)) and (x,y) == tuple(row['pair_point'])
    assert (x,y) in fixed.pair_points(code,row['rotation'])
    all_columns.update((ca,cb))
    sum_point = fixed.e.add(sum_point,(x,y))
assert len(all_columns) == 8
assert sum_point == fixed.e.frob(target,orientation)
assert fixed.e.frob(sum_point,41-orientation) == target
assert list(sum_point) == audit['oriented_target_point']
assert len((HERE/'audit.stderr').read_text()) > 0
assert len((HERE/'audit_v2.stderr').read_text()) > 0
assert len((HERE/'compile_attempt1.txt').read_text()) > 0
base = json.loads((HERE/'base_audit_result.json').read_text())
assert base['status'] == 'PASS_INDEPENDENT_N41_BASE_AUDIT'
assert base['protocol_sha256'] == sha(HERE/'base_audit_protocol.json')
assert [(r['width'],r['usable_base_points'],r['effective_folded_columns'])
        for r in base['rows']] == [(11,1124,557),(10,520,255),(9,284,139)]

w10query = json.loads((HERE/'w10/query_result.json').read_text())
w10audit = json.loads((HERE/'w10/audit_result.json').read_text())
w9query = json.loads((HERE/'w9/query_result.json').read_text())
for width in (10,9):
    sub=HERE/f'w{width}'
    prep_protocol=json.loads((sub/'prepare_protocol.json').read_text())
    prep_result=json.loads((sub/'prepare_result.json').read_text())
    assert prep_protocol['parent_input_sha256']==sha(HERE/'join4_input.tsv')
    assert prep_protocol['script_sha256']==sha(sub/'prepare.py')
    assert prep_result['protocol_sha256']==sha(sub/'prepare_protocol.json')
    assert prep_result['input_sha256']==sha(sub/f'join4_w{width}_input.tsv')
assert w10query['status'] == 'COMPLETE_HIT' and w10query['exit_code'] == 0
assert w10query['protocol_sha256'] == sha(HERE/'w10/query_protocol.json')
assert w10query['stdout_sha256'] == sha(HERE/'w10/join4.stdout')
assert w10query['stderr_sha256'] == sha(HERE/'w10/join4.stderr')
assert w10query['wall_seconds'] <= 600 and w10query['sampled_peak_combined_rss_bytes'] < 4294967296
assert w10audit['status'] == 'PASS_INDEPENDENT_N41_W10_FOURPAIR_PUBLIC_RELATION'
assert w10audit['protocol_sha256'] == sha(HERE/'w10/audit_protocol.json')
assert w10audit['distinct_folded_columns'] == 8
assert w10audit['raw_group_sum_matches_target'] and w10audit['back_transport_matches_public_target']
assert w10audit['projected_subgroup_sum_matches_target']
assert w10audit['orientation'] == 29 and w10audit['source_codes'] == [177,16,267,284]
w10hit=w10query['terminal_line'].split()
assert w10hit[0] == 'HIT' and int(w10hit[1]) == 29
w10ids=[int(x) for x in w10hit[2:6]]
w10states={}
for line in (HERE/'w10/join4_w10_input.tsv').read_text().splitlines():
    p=line.split()
    if p and p[0] == 'S':
        w10states[(int(p[1]),int(p[2]))]=tuple(map(int,p[3:]))
assert len(w10states)==4*520
w10sum=None;w10cols=set()
for slot,sid in enumerate(w10ids):
    code,branch,a,b,ca,cb,x,y=w10states[(slot,sid)]
    assert code == w10audit['rows'][slot]['source_code']
    assert fixed.source_valid(a) and fixed.source_product(code)==fixed.f.mul(a,b)
    assert fixed.column(a)==ca and fixed.column(b)==cb
    assert (x,y) in fixed.pair_points(code,[0,12,24,36][slot])
    w10sum=fixed.e.add(w10sum,(x,y));w10cols.update((ca,cb))
assert len(w10cols)==8 and w10sum==fixed.e.frob(target,29)
assert fixed.e.frob(w10sum,12)==target

assert w9query['status'] == 'COMPLETE_NO_HIT' and w9query['exit_code'] == 0
assert w9query['protocol_sha256'] == sha(HERE/'w9/query_protocol.json')
assert w9query['stdout_sha256'] == sha(HERE/'w9/join4.stdout')
assert w9query['stderr_sha256'] == sha(HERE/'w9/join4.stderr')
assert w9query['wall_seconds'] <= 600 and w9query['sampled_peak_combined_rss_bytes'] < 4294967296
assert w9query['terminal_line'].startswith('NO_HIT 41 ')
assert sum(x.startswith('ORIENTATION_DONE ') for x in w9query['worker_lines']) == 41
print(json.dumps({'status':'PASS_ARCHIVE_VERIFICATION',
                  'relations':['N41_W11_fourpair_public','N41_W10_fourpair_public'],
                  'w11_orientation':orientation,'w10_orientation':29,
                  'w9_status':'COMPLETE_NO_HIT_41_ORIENTATIONS',
                  'distinct_folded_columns':len(all_columns),
                  'sampled_n131_widths':[33,34],
                  'frozen_source_hash_checks':len(checks)},sort_keys=True))
