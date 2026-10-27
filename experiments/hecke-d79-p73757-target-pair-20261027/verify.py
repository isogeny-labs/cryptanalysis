"""Validate frozen target, producer, independent replay and proof receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def read(name):
    return json.loads((HERE/name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan=read('inputs.json')
    for item in plan['frozen'].values():
        assert sha(ROOT/item['path'])==item['sha256']
    pre_target=read('pre-target.json')
    assert sha(HERE/'inputs.json')==pre_target['inputs_sha256']
    assert sha(HERE/'make_target.py')==pre_target['generator_sha256']
    pre=read('pre-run.json')
    for name,expected in pre['sha256'].items():
        assert sha(HERE/name)==expected
    post=read('post_run.json')
    for name,key in [('result.json','result_sha256'),('audit_sage.py','audit_source_sha256'),
                     ('public-target.json','public_target_sha256'),('fixture.json','fixture_sha256')]:
        assert sha(HERE/name)==post[key]
    result=read('result.json');audit=read('audit.json')
    public=read('public-target.json');fixture=read('fixture.json')
    assert result['status']=='VERIFIED_PAIR' and audit['status']=='PASS'
    assert result['target']==audit['target']==public['point']==fixture['point']
    assert result['recovered_scalar']==fixture['scalar']==audit['scalar']==86
    assert result['witness']==audit['witness']==[1,-1,4,1]
    assert result['index_enumerated_patterns']==audit['enumerated_patterns']==3120
    assert result['index_distinct_points']==audit['index_points']==199
    assert result['actual_distinct_projected_base_points']==36
    assert result['candidate_id'] is None and result['target_online_ms'] is None
    assert result['component_phase_sum_ns']+result['target_interval_overhead_ns']==result['component_online_ns']
    cert=read('formal/certificate.json')
    assert cert['witness']==result['witness'] and cert['recovered_scalar']==86
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build and 'error:' not in build
    final=read('post_audit.json')
    for name,expected in final['sha256'].items():
        assert sha(HERE/name)==expected,(name,expected)
    print('PASS: frozen target, pair index, independent scalar replay and Lean proof')


if __name__=='__main__':
    main()
