"""Verify frozen prospective selection, source order, stage receipts and audit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


def main():
    plan,preclass=read('inputs.json'),read('pre-class.json')
    postclass,presource=read('post-class.json'),read('pre-source.json')
    postsource,preaudit=read('post-source.json'),read('pre-audit.json')
    cls,source,audit=read('class-result.json'),read('source-result.json'),read('audit.json')
    sealed=read('post_audit.json')
    assert preclass['inputs_sha256']==sha(HERE/'inputs.json')
    assert preclass['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    assert preclass['class_producer_sha256']==sha(HERE/'prescreen_class.py')
    for item in plan['frozen'].values():
        assert sha(ROOT/item['path'])==item['sha256']
    assert postclass['pre_class_sha256']==sha(HERE/'pre-class.json')
    assert postclass['class_result_sha256']==sha(HERE/'class-result.json')
    assert postclass['class_stdout_sha256']==sha(HERE/'class-stdout.txt')
    assert postclass['class_stderr_sha256']==sha(HERE/'class-stderr.txt')
    assert postclass['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.txt')
    assert presource['inputs_sha256']==sha(HERE/'inputs.json')
    assert presource['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    assert presource['post_class_sha256']==sha(HERE/'post-class.json')
    assert presource['class_result_sha256']==sha(HERE/'class-result.json')
    assert presource['source_runner_sha256']==sha(HERE/'run_sources.py')
    order=cls['selected']['source_order']
    assert presource['source_order']==order
    assert presource['source_order_sha256']==hashlib.sha256(json.dumps(order,separators=(',',':')).encode()).hexdigest()
    assert postsource['pre_source_sha256']==sha(HERE/'pre-source.json')
    assert postsource['source_result_sha256']==sha(HERE/'source-result.json')
    assert postsource['source_stdout_sha256']==sha(HERE/'source-stdout.txt')
    assert postsource['source_stderr_sha256']==sha(HERE/'source-stderr.txt')
    assert preaudit['post_class_sha256']==sha(HERE/'post-class.json')
    assert preaudit['post_source_sha256']==sha(HERE/'post-source.json')
    assert preaudit['audit_script_sha256']==sha(HERE/'audit_sage.py')
    assert cls['status']=='CLASS_READY' and cls['selected']['p']==78157
    assert cls['selected']['largest_prime_factor']==1303
    assert source['status']=='CAP40_RANK_DEFICIT' and source['stop_source_count']==40
    assert source['baseline_rank_mod_q']==32 and len(source['source_entries'])==40
    assert all(x['status']=='OUTSIDE_CLASS_TRACE' for x in source['source_entries'])
    assert [x['source_count'] for x in source['checkpoints']]==plan['checkpoints']
    assert [x['rank_mod_q'] for x in source['checkpoints']]==[32,32,32,32,32,32,33,33]
    assert audit['status']=='PASS' and audit['source_group_equations_verified']==40
    assert audit['hecke_group_rows_verified']==194
    assert audit['hecke_residue1_source_histogram']=={'0':1,'2':193}
    assert len(audit['hecke_candidate_supports'])==194
    assert all(len(x)==4 and x==sorted(set(x)) for x in audit['hecke_candidate_supports'])
    assert [x['rank_mod_q'] for x in audit['old_priority_checkpoints']]==[32,32,32,32,32,33,33,33]
    assert source['candidate_id'] is None and source['target_online_ms'] is None
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build
    assert build.count('does not depend on any axioms')==4 and 'sorryAx' not in build
    lean=(HERE/'formal/ResidueSupport.lean').read_text()
    assert 'sorry' not in lean and 'admit' not in lean
    for name,expected in sealed['sha256'].items():
        assert sha(HERE/name)==expected,name
    print('PASS: prospective p78157 selection, frozen source order, eight rank checkpoints and independent Sage replay')


if __name__=='__main__':
    main()
