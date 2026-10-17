"""Replay frozen hashes and terminal equalities for the code-linear experiment."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
for name in ['protocol.json','audit_protocol.json','benchmark_protocol.json']:
    protocol=read(name)
    for path,digest in protocol['sources'].items():
        assert sha(path)==digest,(name,path)
producer=read('native_result.json');receipt=read('receipt.json')
audit=read('audit_result.json');audit_receipt=read('audit_receipt.json')
assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
assert receipt['protocol_sha256']==sha(HERE/'protocol.json')
assert receipt['native_result_sha256']==sha(HERE/'native_result.json')
assert producer['status']=='COMPLETE_CODE_LINEAR'
assert audit_receipt['status']=='PASS' and audit_receipt['exit_code']==0
assert audit_receipt['protocol_sha256']==sha(HERE/'audit_protocol.json')
assert audit_receipt['audit_result_sha256']==sha(HERE/'audit_result.json')
assert audit['status']=='PASS_CODE_LINEAR_EQUIVALENCE'
assert producer['valid_codes']==audit['codes']==132045
assert producer['left_roots']==audit['left_roots']==audit['right_roots']==264090
for mode,expected in [('positive',1),('ordinary',0)]:
    assert producer[mode]['left']==264090
    assert producer[mode]['full_span']==producer[mode]['source']==producer[mode]['distinct']==expected
    assert producer[mode]['exceptional']==producer[mode]['rank_defect']==producer[mode]['root_fallback']==0
    assert audit[mode]['roots']==audit[mode]['equation_checks']==528180
    assert audit[mode]['reference']==audit[mode]['linear']==expected
    assert audit[mode]['zero']==audit[mode]['exceptional']==audit[mode]['rank_defect']==0
assert producer['positive']['hits'][0]['codes']==[3,16722]
lean=(HERE/'lean.stdout.txt').read_text()
for theorem in ['scaled_product','source_implies_linearized',
                'linearized_implies_s3','linearized_implies_pair']:
    assert f"'CodeLinear.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
assert 'error:' not in lean and (HERE/'lean.stderr.txt').read_text()==''
assert all(bad not in (HERE/'CodeLinear.lean').read_text() for bad in ['sorry','admit','sorryAx'])
pair=read('paired_cpu_result.json');p=read('benchmark_protocol.json')
assert pair['status']=='COMPLETE' and pair['protocol_sha256']==sha(HERE/'benchmark_protocol.json')
assert len(pair['rows'])==len(p['order'])
for index,row in enumerate(pair['rows']):
    arm,mode=p['order'][index]
    assert (row['arm'],row['mode'])==(arm,mode)
    assert row['exit_code']==0 and not row['timed_out']
    data=read(f'paired_{index:02}_{arm}_{mode}.json')
    assert sha(HERE/f'paired_{index:02}_{arm}_{mode}.json')==row['result_sha256']
    assert data['status']==('COMPLETE_CODE_LINEAR_SINGLE' if arm=='code' else 'COMPLETE_BATCHED_QUADRATIC_QUERY')
    assert data['mode']==mode and data['valid_codes']==132045 and data['left_roots']==264090
    q=data['query'];expected=1 if mode=='positive' else 0
    assert q['left']==264090
    assert q['distinct' if arm=='code' else 'distinct_column_hits']==expected
    assert [hit['codes' if arm=='code' else 'codes'] for hit in q['hits']]==([[3,16722]] if expected else [])
by_mode={mode:{arm:[] for arm in ['code','batch']} for mode in ['positive','ordinary']}
for row in pair['rows']:by_mode[row['mode']][row['arm']].append(row['child_cpu_s'])
ratios={mode:sum(v['batch'])/sum(v['code']) for mode,v in by_mode.items()}
result={'status':'PASS','producer_sha256':sha(HERE/'native_result.json'),
        'audit_sha256':sha(HERE/'audit_result.json'),
        'paired_cpu_sha256':sha(HERE/'paired_cpu_result.json'),
        'child_cpu_batch_over_code':ratios,
        'candidate_id':None}
(HERE/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
