"""Cross-link the frozen same-target triple run and independent evidence."""
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
    pre=read('pre-run.json')
    assert sha(HERE/'inputs.json')==pre['inputs_sha256']
    assert sha(HERE/'run.py')==pre['runner_sha256']
    post=read('post-run.json')
    assert sha(HERE/'result.json')==post['result_sha256']
    assert sha(HERE/'audit_sage.py')==post['audit_source_sha256']
    assert sha(HERE/'inputs.json')==post['inputs_sha256']
    run=read('result.json');audit=read('audit.json')
    assert run['status']=='VERIFIED_TRIPLE' and audit['status']=='PASS'
    assert run['target']==audit['target']==[31493,39327]
    assert run['recovered_scalar']==audit['scalar']==973
    assert run['witness']==audit['first_witness']==[7,1,28,1,2,1]
    assert run['probe_count']==audit['first_probe_count']==6
    assert len(run['probes'])==6 and all(x['status']=='MISS' for x in run['probes'][:5])
    assert run['probes'][-1]['status']=='MATCH'
    assert run['pair_index_points']==audit['pair_index_points']==689
    assert audit['triple_patterns']==79040 and audit['triple_coverage_points']==2503
    assert audit['triple_uncovered_points']==28 and audit['target_covered']
    assert run['component_phase_sum_ns']+run['target_interval_overhead_ns']==run['component_online_ns']
    assert run['candidate_id'] is None and run['target_online_ms'] is None
    cert=read('formal/certificate.json')
    assert cert['witness']==run['witness'] and cert['recovered_scalar']==973
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build and 'error:' not in build
    final=read('post_audit.json')
    for name,expected in final['sha256'].items():
        assert sha(HERE/name)==expected,(name,expected)
    print('PASS: retained pair miss, six triple probes, scalar replay and Lean certificates')


if __name__=='__main__':
    main()
