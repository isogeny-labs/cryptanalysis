"""Read-only source, interpolation, full-cube, and group-certificate audit."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):return json.loads((HERE/name).read_text())
def field_mul(x,y):
    result=0;mask=(1<<41)-1
    while y:
        if y&1:result^=x
        y>>=1;carry=x&(1<<40);x=(x<<1)&mask
        if carry:x^=9
    return result
def eval_poly(coeffs,x):
    dense=[0]*17
    for degree,c in coeffs:dense[degree]=c
    value=0
    for c in reversed(dense):value=field_mul(value,x)^c
    return value
proto=load('protocol_v2.json')
files={'parent_v2':HERE/'parent_v2.py','sample_sage':HERE/'sample_sage.py',
       'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'prior':ROOT/'n41_w8_three_pair_resultant_20261013/result.json',
       'witness_archived':OLD/'result.json','negative_archived':OLD/'control_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
assert proto['source_sha256']=={k:sha(p) for k,p in files.items()}
assert proto['sample_first_products']==load('protocol.json')['sample_first_products']
assert proto['holdout_first_products']==load('protocol.json')['holdout_first_products']
assert len(proto['sample_first_products'])==17 and len(set(proto['sample_first_products']+proto['holdout_first_products']))==19
interpolation_comparisons=0
for panel in proto['panel_order']:
    result=load(f'{panel}_result_v2.json')
    assert result['protocol_sha256']==sha(HERE/'protocol_v2.json')
    assert result['source_sha256']==proto['source_sha256']
    assert result['status']=='PASS_ISOLATED_FIRST_PRODUCT_INTERPOLATION'
    assert result['sample_count']==17 and result['universal_terms']==213
    assert result['max_first_product_degree']==16
    assert result['combined_rss_upper_bound_bytes']<proto['rss_boundary_bytes']
    assert len(result['children'])==19
    tensor={(i,j):coeffs for i,j,coeffs in result['coefficient_terms']}
    assert len(tensor)==213
    values=proto['sample_first_products']+proto['holdout_first_products']
    for index,(p,receipt) in enumerate(zip(values,result['children'])):
        stem=f'{panel}_{index:02d}_{p}'
        stdout=HERE/'rows'/f'{stem}.stdout.txt';stderr=HERE/'rows'/f'{stem}.stderr.txt'
        assert sha(stdout)==receipt['stdout_sha256'] and sha(stderr)==receipt['stderr_sha256']
        assert stderr.read_text()=='' and receipt['first_product']==p
        child=json.loads(stdout.read_text())
        assert child['panel']==panel and child['first_product']==p
        assert child['peak_self_rss_raw']==receipt['peak_self_rss_raw']
        predicted={(i,j):eval_poly(coeffs,p) for (i,j),coeffs in tensor.items()}
        predicted={key:value for key,value in predicted.items() if value}
        direct={(i,j):c for i,j,c in child['terms']}
        assert predicted==direct,(panel,p)
        interpolation_comparisons+=len(tensor)
    archived=json.loads(files[f'{panel}_archived'].read_text())
    first_p=proto['holdout_first_products'][0]
    expected={(exps[0],exps[1]):c for exps,c in archived['terms']}
    predicted={(i,j):eval_poly(coeffs,first_p) for (i,j),coeffs in tensor.items()}
    assert {key:v for key,v in predicted.items() if v}==expected
sweep_proto=load('sweep_protocol.json');sweep=load('sweep_result.json')
assert sweep['protocol_sha256']==sha(HERE/'sweep_protocol.json')
assert sweep['source_sha256']=={k:sha(HERE/f'{k}.py') if k=='sweep' else sha(
    ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json' if k=='geometry' else
    ROOT/'n41_w8_three_pair_resultant_20261013/result.json' if k=='prior' else
    HERE/('witness_result_v2.json' if k=='witness_tensor' else 'negative_result_v2.json' if k=='negative_tensor' else 'sage_runtime_info.json'))
    for k in sweep_proto['source_sha256']}
assert sweep['peak_self_rss_raw']<sweep_proto['rss_boundary_bytes']
assert [x['zero_count'] for x in sweep['panels']]==[1,0]
assert all(x['code_triples']==64000 for x in sweep['panels'])
tensor_audit=load('tensor_audit_result.json')
assert tensor_audit['status']=='PASS_REVERSE_ORDER_FULL_CUBE_AUDIT'
tensor_protocol=load('tensor_audit_protocol.json')
tensor_files={'audit_tensor_sage':HERE/'audit_tensor_sage.py',
              'sweep_result':HERE/'sweep_result.json',
              'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
              'witness_tensor':HERE/'witness_result_v2.json',
              'negative_tensor':HERE/'negative_result_v2.json',
              'runtime':HERE/'sage_runtime_info.json'}
assert tensor_audit['source_sha256']==tensor_protocol['source_sha256']=={k:sha(p) for k,p in tensor_files.items()}
assert tensor_audit['protocol_sha256']==sha(HERE/'tensor_audit_protocol.json')
assert [x['zeros'] for x in tensor_audit['panels']]==[1,0]
assert all(x['evaluations']==64000 for x in tensor_audit['panels'])
group=load('audit_result_v2.json')
assert group['status']=='PASS_INTERPOLATED_SWEEP_GROUP_AUDIT'
group_protocol=load('audit_protocol_v2.json')
group_files={'audit_sage_v2':HERE/'audit_sage_v2.py',
             'sweep_result':HERE/'sweep_result.json',
             'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
             'public':ROOT/'n41_w8_fixedseed_ordinary_join_20261013/protocol.json',
             'runtime':HERE/'sage_runtime_info.json'}
assert group['source_sha256']==group_protocol['source_sha256']=={k:sha(p) for k,p in group_files.items()}
assert group['protocol_sha256']==sha(HERE/'audit_protocol_v2.json')
assert group['panels'][0]['signed_state_combinations_checked']==64
assert group['panels'][0]['group_hits']==[{'state_ids':[97,151,42,0,14,109,51],
    'masks':[153,215,64],'products':[97508,1383481007416,216004441708],
    'distinct_columns':14}]
assert group['panels'][1]['group_hits']==[]
failed=load('attempt1_resource.json')
assert failed['status']=='RESOURCE_LIMIT_VIOLATION' and failed['peak_self_rss_raw_bytes']>failed['rss_boundary_bytes']
assert failed['protocol_sha256']==sha(HERE/'protocol.json')
audit_failed=load('audit_attempt1.json')
assert audit_failed['status']=='PRODUCER_FAILURE'
assert audit_failed['first_protocol_sha256']==sha(HERE/'audit_protocol.json')
out={'status':'PASS','interpolation_coefficient_checks':interpolation_comparisons,
     'full_cube_evaluations_independent':128000,'group_witness_state_ids':[97,151,42,0,14,109,51],
     'preserved_failures':2,'panel_rss_upper_bounds_bytes':[
         load(f'{p}_result_v2.json')['combined_rss_upper_bound_bytes'] for p in proto['panel_order']]}
(HERE/'verification.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
