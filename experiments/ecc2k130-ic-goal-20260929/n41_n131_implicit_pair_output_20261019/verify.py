"""Read-only archive audit for both implicit membership and terminal gates."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())


def main():
    build=load(HERE/'build_result.json')
    assert build['status']=='PASS_NATIVE_BUILDS'
    for binary,rec in build['entries'].items():
        assert sha(HERE/binary)==rec['binary_sha256']
        assert sha(HERE/(binary+'.cpp'))==rec['source_sha256']
    prep=load(HERE/'prepare_result.json')
    assert prep['status']=='PASS_IMPLICIT_PAIR_PREPARATION'
    assert prep['protocol_sha256']==sha(HERE/'prepare_protocol_v2.json')
    assert prep['script_sha256']==sha(HERE/'prepare_sage.py')
    for case in prep['cases']:assert sha(case['path'])==case['sha256']
    terminal_prep=load(HERE/'terminal_prepare_result.json')
    assert terminal_prep['status']=='PASS_IMPLICIT_TERMINAL_PREPARATION'
    assert terminal_prep['protocol_sha256']==sha(HERE/'terminal_prepare_protocol.json')
    assert terminal_prep['script_sha256']==sha(HERE/'prepare_terminal_sage.py')
    for case in terminal_prep['cases']:assert sha(case['path'])==case['sha256']
    assert load(HERE/'prepare_failure_v1.json')['status']=='PRODUCER_ASSERTION_FAILURE'
    assert load(HERE/'audit_failure_n41_v1.json')['status']=='AUDITOR_PARSE_FAILURE'
    checks=[]
    for label in ['n41','n131']:
        cfg=load(HERE/f'query_protocol_{label}.json')
        receipt=load(HERE/f'{label}.receipt.json')
        audit=load(HERE/f'audit_result_{label}.json')
        assert cfg['worker_count']==1 and cfg['wall_cap_seconds']==120
        assert cfg['rss_cap_bytes']==4294967296 and cfg['candidate_id'] is None
        assert sha(HERE/'supervise.py')==cfg['supervisor_sha256']
        for rec in [cfg['binary'],cfg['input'],*cfg['dependencies'].values()]:
            assert sha(rec['path'])==rec['sha256']
        assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
        assert receipt['protocol_sha256']==sha(HERE/f'query_protocol_{label}.json')
        assert receipt['stdout_sha256']==sha(HERE/f'{label}.stdout')
        assert receipt['stderr_sha256']==sha(HERE/f'{label}.stderr')
        assert receipt['sampled_peak_combined_rss_bytes']<4294967296
        assert audit['status']==f'PASS_IMPLICIT_PAIR_AUDIT_{label.upper()}'
        assert audit['stdout_sha256']==sha(HERE/f'{label}.stdout')
        tcfg=load(HERE/f'terminal_query_protocol_{label}.json')
        treceipt=load(HERE/f'terminal_{label}.receipt.json')
        taudit=load(HERE/f'terminal_audit_result_{label}.json')
        assert tcfg['worker_count']==1 and tcfg['wall_cap_seconds']==120
        assert tcfg['rss_cap_bytes']==4294967296 and tcfg['candidate_id'] is None
        assert sha(HERE/'supervise_terminal.py')==tcfg['supervisor_sha256']
        for rec in [tcfg['binary'],tcfg['input'],*tcfg['dependencies'].values()]:
            assert sha(rec['path'])==rec['sha256']
        assert treceipt['status']=='COMPLETE' and treceipt['exit_code']==0
        assert treceipt['protocol_sha256']==sha(HERE/f'terminal_query_protocol_{label}.json')
        assert treceipt['stdout_sha256']==sha(HERE/f'terminal_{label}.stdout')
        assert treceipt['stderr_sha256']==sha(HERE/f'terminal_{label}.stderr')
        assert treceipt['sampled_peak_combined_rss_bytes']<4294967296
        assert taudit['status']==f'PASS_IMPLICIT_TERMINAL_AUDIT_{label.upper()}'
        assert taudit['stdout_sha256']==sha(HERE/f'terminal_{label}.stdout')
        assert taudit['membership_hits']==1
        checks.append({'label':label,'member_query_ns':audit['native_query_ns'],
                       'terminal_query_ns':taudit['native_query_ns'],
                       'terminal_roots':taudit['right_roots_replayed'],
                       'terminal_hits':taudit['membership_hits']})
    lean=(HERE/'lean.stdout').read_text()
    assert lean.count('depends on axioms: [propext, Classical.choice, Quot.sound]')==3
    assert not (HERE/'lean.stderr').read_text()
    assert 'sorry' not in (HERE/'PairOutputRecovery.lean').read_text()
    result={'status':'PASS_IMPLICIT_PAIR_ARCHIVE','candidate_id':None,
            'checks':checks,'lean_source_sha256':sha(HERE/'PairOutputRecovery.lean'),
            'lean_stdout_sha256':sha(HERE/'lean.stdout'),
            'script_sha256':sha(__file__)}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
