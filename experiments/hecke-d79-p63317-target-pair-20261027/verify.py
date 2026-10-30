"""Cross-link frozen class, target, coverage, audit and Lean receipts."""
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
    prelogs=read('pre-logs.json')
    assert sha(HERE/'inputs.json')==prelogs['inputs_sha256']
    assert sha(HERE/'prepare_logs.py')==prelogs['producer_sha256']
    postlogs=read('post-logs.json')
    for name,expected in postlogs['sha256'].items():
        assert sha(HERE/name)==expected
    pretarget=read('pre-target.json')
    assert sha(HERE/'inputs.json')==pretarget['inputs_sha256']
    assert sha(HERE/'class-logs.json')==pretarget['class_logs_sha256']
    assert sha(HERE/'make_target.py')==pretarget['generator_sha256']
    prerun=read('pre-run.json')
    for name,expected in prerun['sha256'].items():
        assert sha(HERE/name)==expected
    postrun=read('post-run.json')
    for name,key in [('result.json','result_sha256'),('audit_sage.py','audit_source_sha256'),
                     ('public-target.json','public_target_sha256'),('fixture.json','fixture_sha256'),
                     ('class-logs.json','class_logs_sha256')]:
        assert sha(HERE/name)==postrun[key]
    logs=read('class-logs.json');fixture=read('fixture.json')
    run=read('result.json');audit=read('audit.json');sums=read('sumset-audit.json')
    assert logs['status']==audit['status']==sums['status']=='PASS'
    assert run['status']=='NO_RELATION' and run['recovered_scalar'] is None
    assert fixture['scalar']==audit['fixture_scalar']==sums['target_scalar']==973
    assert run['target']==audit['target']==fixture['point']
    assert run['index_distinct_points']==audit['index_points']==sums['distinct_covered_scalars']==689
    assert run['index_enumerated_patterns']==audit['pair_patterns']==sums['signed_pattern_count']==3120
    assert sums['signed_equals_sumset'] and not sums['target_covered']
    assert sums['unordered_sum_patterns']==820 and len(sums['covered_scalars'])==689
    assert run['candidate_id'] is None and run['target_online_ms'] is None
    assert run['component_phase_sum_ns']+run['target_interval_overhead_ns']==run['component_online_ns']
    cert=read('formal/certificate.json')
    assert cert['target_scalar']==973 and cert['distinct_covered']==689
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build and 'error:' not in build
    post=read('post_audit.json')
    for name,expected in post['sha256'].items():
        assert sha(HERE/name)==expected,(name,expected)
    print('PASS: frozen p63317 target miss, exact sumset, independent Sage audit and Lean certificates')


if __name__=='__main__':
    main()
