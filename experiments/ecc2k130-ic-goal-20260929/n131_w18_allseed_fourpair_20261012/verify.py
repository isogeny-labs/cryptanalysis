"""Verify frozen source, run, formula, and proof receipts for this experiment."""
import hashlib,json
from pathlib import Path
h=Path(__file__).resolve().parent
root=h.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
# Exact-shield source and every frozen v2 construction input.
p=read(h/'v2_protocol.json')
paths={'script':h/'v2_build.py','builder':h/'fourpair_v2.py',
       'n41_fixture':h/'n41_diagonal/control_fixture.json',
       'n131_fixture':h/'n131_control_fixture.json',
       'n41_support':root/'n41_w7_entropy_cubic_20261011/w8/geometry.json',
       'n131_support':root/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv',
       'public_target':root/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert sha(h/'v2_run.py')==p['runner_sha256']
for mode in ('n41_control','n131_control','n131_public'):
    r=read(h/f'v2_{mode}_receipt.json');j=read(h/f'v2_{mode}.json')
    assert r['status']=='PASS' and r['stop_reason'] is None and r['exit_code']==0
    assert r['parent_wall_ns']<600*10**9 and r['peak_combined_rss_bytes_sampled']<4*1024**3
    assert r['protocol_sha256']==j['protocol_sha256']==sha(h/'v2_protocol.json')
    assert r['result_sha256']==sha(h/f'v2_{mode}.json')
    assert j['formula_sha256']==sha(h/f'v2_{mode}.xcnf')
    assert j['metadata']['source_masks']==(125 if mode=='n41_control' else 131307)
    assert j['metadata']['same_column_mask_pairs']==(12 if mode=='n41_control' else 243)
    assert j['metadata']['folded_column_shield_clauses']==(672 if mode=='n41_control' else 13608)
    if mode!='n131_public':assert j['control_check']['status']=='PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT'
# Independent N41 diagonal-source row, its raw public point, and bounded SAT attempts.
a=read(h/'n41_diagonal/audit_result.json');d=read(h/'n41_diagonal/receipt.json')
assert a['status']=='PASS_INDEPENDENT_N41_DIAGONAL_ALLSEED_FOURPAIR_RELATION'
assert a['pair_count']==4 and a['distinct_folded_columns']==8
assert a['rank_with_prior_rows']==4 and a['prior_rank']==3
assert a['public_target']==[920359962848,755404565011]
assert d['hit_line'] in (h/'n41_diagonal/stdout.log').read_text().splitlines()
assert d['runner_wall_ns']<180*10**9 and d['peak_combined_rss_bytes_sampled']<4*1024**3
v2=read(h/'n41_solver_receipt_v2.json');v3=read(h/'n41_solver_receipt_v3.json')
assert v2['status']=='BOUNDED_UNKNOWN' and v2['solver_terminal_lines']==['s INDETERMINATE']
assert v3['status']=='BOUNDED_UNKNOWN' and v3['stop_reason']=='WALL_CAP'
assert v3['solver_terminal_lines']==[] and v3['exit_code']==-9
assert v3['stdout_sha256']==sha(h/'n41_solver_v3.stdout')
assert sha(h/'v2_n41_control.xcnf')==read(h/'solver_protocol_v3.json')['sha256']['formula']
lean=(h/'lean_check.txt').read_text()
assert 'sorryAx' not in lean and 'FourPairSupport.fourTuples_length' in lean
assert 'Quot.sound' in lean and 'propext' in lean
print('PASS_FROZEN_ALLSEED_FOURPAIR_EVIDENCE')
