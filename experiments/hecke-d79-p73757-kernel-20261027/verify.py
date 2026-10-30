"""Check frozen dependencies, receipts and final kernel mechanism claims."""
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
    assert sha(HERE/'produce.py')==pre['producer_sha256']
    post=read('post_run.json')
    assert sha(HERE/'result.json')==post['result_sha256']
    assert sha(HERE/'audit.py')==post['audit_source_sha256']
    assert sha(HERE/'inputs.json')==post['inputs_sha256']
    anchor=read('anchor-plan.json')
    for name,key in [('inputs.json','inputs_sha256'),('result.json','result_sha256'),
                     ('anchor-audit.json','anchor_audit_sha256')]:
        assert sha(HERE/name)==anchor[key]
    result=read('result.json')
    audit=read('audit.json')
    anchors=read('anchor-audit.json')
    solve=read('anchor-solve.json')
    assert result['status']=='COMPLETE' and audit['status']=='PASS'
    assert anchors['status']=='PASS' and solve['status']=='PASS'
    assert (result['p'],result['q'],result['anchor_index'])==(73757,199,0)
    assert solve['recovered_q_logs']==result['q_logs']
    assert len(result['q_logs'])==40 and all(result['q_logs'])
    for name in ('support4_plus_direct5','support4_plus_hecke5','support4_plus_both5'):
        assert result['families'][name]['rank_mod_q']==39
        assert result['families'][name]['normalized_unique_kernel']==result['q_logs']
        assert all(x==40 for x in anchors['families'][name]['ranks_after_anchor'])
    cert=read('formal/certificate.json')
    assert cert['rows']==706 and cert['selected_minor_size']==39
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build and 'error:' not in build
    final=read('post_audit.json')
    for name,expected in final['sha256'].items():
        assert sha(HERE/name)==expected,(name,expected)
    print('PASS: parent identity, group/log audits, anchors, solve and Lean certificates')


if __name__=='__main__':
    main()
