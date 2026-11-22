"""Read-only receipt and cross-result audit for the free-code RR screen."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
read=lambda name:json.loads((HERE/name).read_text())
protocol_names=('protocol_n41.json','protocol_n41_root0.json',
                'prepare_protocol_n131.json','protocol_n131.json',
                'prepare_protocol_n131_v2.json','protocol_n131_v2.json',
                'audit_protocol_n131.json','span_protocol.json','audit_protocol_span.json')
for name in protocol_names:
    for path,digest in read(name)['sources'].items():assert sha(path)==digest,path
n41=read('result_n41.json')
n41_root0=read('result_n41_root0.json')
n131=read('result_n131.json')
n131_v2=read('result_n131_v2.json')
audit=read('audit_result_n131.json')
certificate=read('span_certificate.json')
span_audit=read('audit_span_result.json')
assert n41['status']=='COMPLETE_N41_CODE_FAMILY_CERTIFICATE_SCREEN'
assert n41['valid_charts']==70 and n41['first_failed_prefix']==2
assert n41_root0['valid_charts']==35 and n41_root0['first_failed_prefix']==2
assert n41_root0['first_full_nonconstant_rank']==2
assert n131['status']=='COMPLETE_N131_CODE_FAMILY_CERTIFICATE_SCREEN'
assert [r['pooled_nonconstant_rank'] for r in n131['rows']]==[34,68,102]
assert all(r['shared_functional_exists'] for r in n131['rows'])
assert n131_v2['status']=='COMPLETE_N131_FOUR_CODE_CERTIFICATE_SCREEN'
assert [r['pooled_nonconstant_rank'] for r in n131_v2['rows']]==[34,68,102,131]
assert n131_v2['first_failed_prefix']==4
assert audit['status']=='PASS_INDEPENDENT_N131_DETERMINANT_RANK_REPLAY'
assert span_audit['status']=='PASS_INDEPENDENT_N131_SPAN_CERTIFICATE_REPLAY'
assert span_audit['span_certificate_sha256']==sha(HERE/'span_certificate.json')
assert certificate['status']=='EXACT_N131_CONSTANT_IN_SIGN_SPAN'
assert certificate['span_rank']==131 and certificate['selected_count']==67
value=0
for row in certificate['selected']:value^=row['field_value']
assert value==certificate['constant']==span_audit['selected_xor']
assert not (HERE/'lean.stderr.txt').read_text()
lean=(HERE/'lean.stdout.txt').read_text()
assert lean.count('depends on axioms: [propext]')==2
for name in ('run_n41.stderr.txt','run_n41_root0.stderr.txt','prepare_n131.stderr.txt',
             'run_n131.stderr.txt','prepare_n131_v2.stderr.txt','run_n131_v2.stderr.txt',
             'audit_n131.stderr.txt','span.stderr.txt','audit_span.stderr.txt'):
    assert not (HERE/name).read_text(),name
result={'status':'PASS_RR_FREE_CODE_TERMINAL_AUDIT','candidate_id':None,
        'n41_root0_first_failure':2,'n131_first_failure':4,
        'n131_span_rank':131,'span_witness_terms':67,
        'sha256':{name:sha(HERE/name) for name in (
            'protocol_n41_root0.json','result_n41_root0.json','protocol_n131_v2.json',
            'result_n131_v2.json','audit_result_n131.json','span_certificate.json',
            'audit_span_result.json','SpanObstruction.lean','lean.stdout.txt')}}
with (HERE/'terminal.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
