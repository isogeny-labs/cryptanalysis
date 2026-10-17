"""Read-only audit of the bounded per-right GCD panels and correction receipt."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
proto=json.loads((HERE/'protocol_v2.json').read_text())
result=json.loads((HERE/'result_v2.json').read_text())
files={'worker_v2':HERE/'worker_v2.py','geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'witness':OLD/'result.json','negative':OLD/'control_result.json',
       'joint':OLD/'joint_result.json','negative_joint':OLD/'control_joint_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
assert proto['source_sha256']==result['source_sha256']=={k:sha(p) for k,p in files.items()}
assert result['protocol_sha256']==sha(HERE/'protocol_v2.json')
assert result['status']=='PASS_PER_RIGHT_LOW_DEGREE_GCD' and result['candidate_id'] is None
assert len(result['panels'])==2
for panel in result['panels']:
    old=json.loads((OLD/('joint_result.json' if panel['name']=='witness' else 'control_joint_result.json')).read_text())
    assert panel['degree_histogram']=={'16':128}
    assert panel['right_products']==panel['left_span_size']==128
    assert panel['valid_right_products']==40
    assert panel['identically_zero_specializations']==0
    assert sorted(set(r for q,r in panel['matches']))==old['panels'][0]['span_roots']
    assert sorted(panel['valid_matches'])==sorted(old['panels'][1]['usable_r_matches'])
    assert panel['specialize_ns']+panel['gcd_ns']+panel['direct_replay_ns']<=panel['panel_ns']
    assert [row['processed'] for row in panel['checkpoints']]==[8,32,128]
assert result['panels'][0]['matches']==[[1383481007416,216004441708]]
assert result['panels'][1]['matches']==[]
failed=json.loads((HERE/'attempt1.json').read_text())
assert failed['status']=='PRODUCER_FAILURE' and failed['exit_code']==1
assert failed['protocol_sha256']==sha(HERE/'protocol.json')
assert result['peak_self_rss_raw']<proto['rss_boundary_bytes']
out={'status':'PASS','panels':2,'right_products_checked':256,
     'direct_q_evaluations':256*128,'gcd_evaluations':256,
     'archived_comparisons':2,'preserved_producer_failures':1}
(HERE/'verification.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
