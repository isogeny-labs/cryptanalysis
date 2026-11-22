"""Read-only terminal check for N41 RR certificate coverage receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda name:json.loads((HERE/name).read_text())
for name in ('protocol.json','audit_protocol.json','fullroot_protocol.json','audit_fullroot_protocol.json'):
    for path,digest in read(name)['sources'].items():assert sha(path)==digest,path
base=read('result.json')
base_audit=read('audit_result.json')
full=read('fullroot_result.json')
full_audit=read('audit_fullroot_result.json')
assert base['status']=='COMPLETE_N41_RR_PAIRWISE_CENSUS'
assert (base['chart_count'],base['pair_count'],base['single_certifiable'],base['pair_certifiable'])==(35,595,35,0)
assert base['pair_nonconstant_rank_distribution']=={'41':595}
assert all(row['nonconstant_rank']==41 and not row['common_functional_exists'] for row in base['pairs'])
assert base_audit['status']=='PASS_INDEPENDENT_N41_PAIRWISE_DETERMINANT_RANK_AUDIT'
assert base_audit['result_sha256']==sha(HERE/'result.json')
assert {int(k):v for k,v in base_audit['pair_rank_distribution'].items()}=={41:595}
assert full['status']=='COMPLETE_N41_BOTH_ROOTS_CERTIFICATE_CENSUS'
assert full['code_count']==35 and full['certifiable_codes']==0
assert full['rank_distribution']=={'41':35}
assert full_audit['status']=='PASS_INDEPENDENT_N41_BOTH_ROOTS_DETERMINANT_RANK_AUDIT'
assert full_audit['fullroot_result_sha256']==sha(HERE/'fullroot_result.json')
assert {int(k):v for k,v in full_audit['rank_distribution'].items()}=={41:35}
assert not (HERE/'lean.stderr.txt').read_text()
assert "'CertificateCoverage.pair_span_obstructs_shared_trace' depends on axioms: [propext]" in (HERE/'lean.stdout.txt').read_text()
for name in ('census.stderr.txt','audit.stderr.txt','fullroot.stderr.txt','audit_fullroot.stderr.txt'):
    assert not (HERE/name).read_text(),name
result={'status':'PASS_N41_RR_CERTIFICATE_COVERAGE_TERMINAL_AUDIT',
        'candidate_id':None,'codes':35,'pairwise_full_rank':595,'both_root_full_rank':35,
        'sha256':{name:sha(HERE/name) for name in (
            'protocol.json','result.json','audit_result.json','fullroot_protocol.json',
            'fullroot_result.json','audit_fullroot_result.json','CertificateCoverage.lean','lean.stdout.txt')}}
with (HERE/'terminal.json').open('x') as out:
    json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(result['status'])
