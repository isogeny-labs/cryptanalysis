"""Independent receipt and arithmetic-status audit for the degree-fall panel."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda path:json.loads(Path(path).read_text())
cfg=read(HERE/'verification_protocol.json')
assert cfg['status']=='FROZEN_BEFORE_TERMINAL_AUDIT'
for name,source in cfg['sources'].items():
    assert sha(source['path'])==source['sha256'],name

failure=read(HERE/'runtime_attempt1_failure.json')
assert failure['status']=='RUNTIME_CHECK_FAILURE_BEFORE_WORKLOAD' and failure['worker_started'] is False
assert read(HERE/'n41_gate.json')['status']=='PASS_N41_CUBIC_CONTROL'
assert read(HERE/'hybrid_n41_gate.json')['status']=='PASS_N41_HYBRID_CONTROL'
scan=read(HERE/'result.json')
profile=read(HERE/'profile_result.json')
assert scan['status']=='COMPLETE_DEGREE_FALL_SCAN'
assert profile['status']=='PASS_CUBIC_PROFILE'
assert len(scan['panels'])==len(profile['panels'])==4
for row in scan['panels']:
    n=row['field_degree']
    assert row['direct_evaluation_checks']==129
    assert row['ranks']['3']['nullity']==0
    if n==41:
        assert row['anf_monomials']==886
        assert row['ranks']['4']['rank']==205
        assert row['ranks']['4']['nullity']==41
    else:
        assert row['anf_monomials']==5317
        assert row['ranks']['4']['rank']==524
        assert row['ranks']['4']['nullity']==131
for row in profile['panels']:
    n=row['field_degree']
    assert row['original_monomials']==(886 if n==41 else 5317)
    assert row['scaled_monomials']==(446 if n==41 else 2314)
    assert row['scaled_degree_histogram']['4']==0
    assert row['assignments_checked']==(32768 if n==41 else 4097)
    if n==41:
        assert row['exceptional_assignments']==0
        assert row['original_zero_assignments']==row['scaled_zero_assignments']

lean=Path(HERE/'lean.stdout').read_text()
assert Path(HERE/'lean.stderr').read_text()==''
assert Path(HERE/'lean_recheck.stderr').read_text()==''
assert Path(HERE/'lean_recheck.stdout').read_text()==lean
for theorem in ('scaled_zero_iff','zero_product_exception','fourth_additive',
                'binary_bit_fourth','scaled_support_degree'):
    assert f"'DegreeFall.{theorem}'" in lean
assert 'sorryAx' not in lean
assert 'sorry' not in Path(HERE/'DegreeFall.lean').read_text()

statuses=[]
for prefix in ('','hybrid_'):
    for case in ('n41_p_k5','n41_o_k5'):
        receipt=read(HERE/(prefix+case+'_receipt.json'))
        result=read(HERE/(prefix+case+'_result.json'))
        assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
        assert receipt['monitor_error'] is None and receipt['stop_reason'] is None
        assert receipt['sampled_peak_combined_rss_bytes']<4294967296
        assert receipt['result_sha256']==sha(HERE/(prefix+case+'_result.json'))
        assert result['status']==('GB_COMPLETE' if '_p_' in case else 'GB_UNIT_IDEAL')
        if '_p_' in case:
            assert result['recovered_codes']=={'first_code':253,'second_code':63}
    case='n131_p_k4'
    receipt=read(HERE/(prefix+case+'_receipt.json'))
    assert receipt['status']=='RSS_CAP' and receipt['stop_reason']=='RSS_CAP'
    assert receipt['exit_code']==-15 and receipt['result_sha256'] is None
    assert receipt['monitor_error'] is None and receipt['rss_samples']>0
    assert receipt['sampled_peak_combined_rss_bytes']>4294967296
    assert receipt['wall_seconds']<600
    assert receipt['stdout_sha256']==sha(HERE/(prefix+case+'.stdout'))
    assert receipt['stderr_sha256']==sha(HERE/(prefix+case+'.stderr'))
    assert not (HERE/(prefix+case+'_result.json')).exists()
    stream=Path(HERE/(prefix+case+'.stdout')).read_text()
    assert stream.count('GB_START')==1 and 'GB_COMPLETE' not in stream
    statuses.append({'formulation':prefix[:-1] if prefix else 'standalone_cubic',
                     'status':'RSS_CAP','wall_seconds':receipt['wall_seconds'],
                     'peak_rss_bytes':receipt['sampled_peak_combined_rss_bytes']})

prior=read(cfg['sources']['prior_quartic_positive']['path'])
assert prior['status']=='GB_COMPLETE'
assert prior['recovered_codes']=={'first_code':3,'second_code':16722}
out={'status':'PASS_TERMINAL_DEGREE_FALL_AUDIT','candidate_id':None,
     'protocol_sha256':sha(HERE/'verification_protocol.json'),
     'verifier_sha256':sha(__file__),'n131_positive_attempts':statuses,
     'n41_cubic_gate':'PASS','n41_hybrid_gate':'PASS',
     'lean_declarations_checked':5}
(HERE/'verification_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
