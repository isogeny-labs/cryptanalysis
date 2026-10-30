"""Verify frozen four-gate series and independent full-source replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())


def main():
    plan,pregate=read('inputs.json'),read('pre-gate.json')
    postgate,prechallenge=read('post-gate.json'),read('pre-challenge.json')
    postchallenge,preaudit=read('post-challenge.json'),read('pre-audit.json')
    gate,challenge,audit=read('gate-result.json'),read('challenge-result.json'),read('audit.json')
    sealed=read('post_audit.json')
    assert pregate['inputs_sha256']==sha(HERE/'inputs.json')
    assert pregate['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    assert pregate['select_runner_sha256']==sha(HERE/'select_series.py')
    for item in plan['frozen'].values():assert sha(ROOT/item['path'])==item['sha256']
    assert postgate['pre_gate_sha256']==sha(HERE/'pre-gate.json')
    assert postgate['gate_result_sha256']==sha(HERE/'gate-result.json')
    assert postgate['gate_stdout_sha256']==sha(HERE/'gate-stdout.txt')
    assert postgate['gate_stderr_sha256']==sha(HERE/'gate-stderr.txt')
    assert postgate['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.txt')
    assert prechallenge['post_gate_sha256']==sha(HERE/'post-gate.json')
    assert prechallenge['gate_result_sha256']==sha(HERE/'gate-result.json')
    assert prechallenge['challenge_script_sha256']==sha(HERE/'run_full_challenges.py')
    assert postchallenge['pre_challenge_sha256']==sha(HERE/'pre-challenge.json')
    assert postchallenge['challenge_result_sha256']==sha(HERE/'challenge-result.json')
    assert postchallenge['challenge_stdout_sha256']==sha(HERE/'challenge-stdout.txt')
    assert postchallenge['challenge_stderr_sha256']==sha(HERE/'challenge-stderr.txt')
    assert preaudit['post_gate_sha256']==sha(HERE/'post-gate.json')
    assert preaudit['post_challenge_sha256']==sha(HERE/'post-challenge.json')
    assert preaudit['audit_script_sha256']==sha(HERE/'audit_sage.py')
    assert gate['status']=='FOUR_GATES_FROZEN' and challenge['status']=='COMPLETE'
    ps=[102077,103357,108557,115237]
    assert [x['p'] for x in gate['selected']]==[x['p'] for x in challenge['cases']]==[x['p'] for x in audit['cases']]==ps
    assert [x['baseline_rank_mod_q'] for x in gate['selected']]==[32,35,31,32]
    assert all(x['gate_decision']=='SKIP' for x in gate['selected'])
    assert [x['full_pool_rank_mod_q'] for x in challenge['cases']]==[34,39,34,35]
    assert all(x['status']=='COMPLETE' and len(x['source_entries'])==40 for x in challenge['cases'])
    assert all(all(e['status']=='OUTSIDE_CLASS_TRACE' for e in x['source_entries']) for x in challenge['cases'])
    expected_counts={'CORRECT_ACCEPT':0,'CORRECT_REJECT':3,'FALSE_ACCEPT':0,'FALSE_REJECT':1,'UNKNOWN':0}
    assert challenge['gate_counts']==audit['gate_counts']==expected_counts
    assert audit['status']=='PASS'
    false=next(x for x in audit['cases'] if x['p']==103357)
    assert false['gate_validation']=='FALSE_REJECT' and false['anchored_log_replay']=='PASS'
    assert len(false['anchored_logs'])==40 and false['anchor_index']==0
    assert challenge['candidate_id'] is None and challenge['target_online_ms'] is None
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build
    assert build.count('does not depend on any axioms')==3 and 'sorryAx' not in build
    lean=(HERE/'formal/DirectRankGateSeries.lean').read_text()
    assert 'sorry' not in lean and 'admit' not in lean
    for name,expected in sealed['sha256'].items():assert sha(HERE/name)==expected,name
    print('PASS: four frozen SKIP decisions, one independently verified false reject and Lean gate logic')


if __name__=='__main__':main()
