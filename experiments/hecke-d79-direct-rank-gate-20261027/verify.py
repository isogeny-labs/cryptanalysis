"""Verify frozen gate decision, full challenge, independent audit and Lean receipt."""
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
    assert pregate['select_runner_sha256']==sha(HERE/'select_gate.py')
    for item in plan['frozen'].values():assert sha(ROOT/item['path'])==item['sha256']
    assert postgate['pre_gate_sha256']==sha(HERE/'pre-gate.json')
    assert postgate['gate_result_sha256']==sha(HERE/'gate-result.json')
    assert postgate['gate_stdout_sha256']==sha(HERE/'gate-stdout.txt')
    assert postgate['gate_stderr_sha256']==sha(HERE/'gate-stderr.txt')
    assert postgate['sage_runtime_sha256']==sha(HERE/'sage-runtime-info.txt')
    assert prechallenge['post_gate_sha256']==sha(HERE/'post-gate.json')
    assert prechallenge['gate_result_sha256']==sha(HERE/'gate-result.json')
    assert prechallenge['challenge_script_sha256']==sha(HERE/'run_full_challenge.py')
    assert postchallenge['pre_challenge_sha256']==sha(HERE/'pre-challenge.json')
    assert postchallenge['challenge_result_sha256']==sha(HERE/'challenge-result.json')
    assert postchallenge['challenge_stdout_sha256']==sha(HERE/'challenge-stdout.txt')
    assert postchallenge['challenge_stderr_sha256']==sha(HERE/'challenge-stderr.txt')
    assert preaudit['post_gate_sha256']==sha(HERE/'post-gate.json')
    assert preaudit['post_challenge_sha256']==sha(HERE/'post-challenge.json')
    assert preaudit['audit_script_sha256']==sha(HERE/'audit_sage.py')
    assert gate['status']=='GATE_FROZEN' and gate['p']==90917 and gate['q']==89
    assert gate['baseline_rank_mod_q']==32 and gate['gate_decision']=='SKIP'
    assert challenge['status']=='COMPLETE' and challenge['gate_validation']=='CORRECT_REJECT'
    assert challenge['full_pool_rank_mod_q']==35 and len(challenge['source_entries'])==40
    assert all(e['status']=='OUTSIDE_CLASS_TRACE' for e in challenge['source_entries'])
    assert audit['status']=='PASS' and audit['baseline_rank_mod_q']==32
    assert audit['full_pool_rank_mod_q']==35 and audit['hecke_group_rows_verified']==201
    assert audit['hecke_support_size_histogram']=={'3':1,'4':200}
    assert audit['hecke_residue1_source_histogram']=={'0':3,'2':197,'4':1}
    assert [x['rank_mod_q'] for x in audit['ascending_checkpoints']]==[32,32,33,33,33,33,33,35]
    assert challenge['candidate_id'] is None and challenge['target_online_ms'] is None
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build
    assert build.count('does not depend on any axioms')==5 and 'sorryAx' not in build
    lean=(HERE/'formal/DirectRankGate.lean').read_text()
    assert 'sorry' not in lean and 'admit' not in lean
    for name,expected in sealed['sha256'].items():assert sha(HERE/name)==expected,name
    print('PASS: pre-lift SKIP decision, 40-source challenge, independent Sage rank and Lean support counts')


if __name__=='__main__':main()
