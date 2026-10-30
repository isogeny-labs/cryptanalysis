"""Verify frozen prefix receipts, retained failures, and checked proofs."""
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post_inputs.json').read_text())
FORMAL = json.loads((HERE / 'formal/inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha(HERE / 'run.py') == PLAN['runner_sha256']
    assert sha(HERE / 'audit.py') == PLAN['auditor_sha256']
    assert sha(HERE / 'audit_v2.py') == POST['auditor_v2_sha256']
    assert (HERE / 'sage-runtime-info.txt').stat().st_size > 0
    assert 'Build completed successfully' in (HERE / 'formal/build-output.txt').read_text()
    build = (HERE / 'formal/build-output.txt').read_text()
    axioms = re.findall(r'depends on axioms: \[([^]]+)\]', build)
    assert all(set(a.replace(' ', '').split(',')) <=
               {'propext', 'Classical.choice', 'Quot.sound'} for a in axioms)
    attempts = []
    for case in PLAN['cases']:
        p = case['p']
        result = HERE / f'p{p}-result.json'
        audit = HERE / f'p{p}-audit-v2.json'
        old_err = HERE / f'p{p}-audit-stderr.txt'
        module = HERE / f'formal/RankPrefixP{p}.lean'
        assert result.exists() and audit.exists() and module.exists()
        assert sha(result) == POST['producer_results'][str(p)]
        data = json.loads(result.read_text())
        check = json.loads(audit.read_text())
        assert check['status'] == 'PASS' and check['producer_sha256'] == sha(result)
        assert data['status'] == 'RANK40_STOP'
        assert data['stop_source_count'] == check['source_count']
        assert data['cumulative_search_trials'] == check['search_trials'] == sum(
            math.comb(data['stop_source_count'], s)*2**(s-1) for s in range(1, 5))
        assert data['sources'][-1]['rank_qq'] == check['final_rank_qq'] == 40
        assert data['sources'][-1]['rank_mod_q'] == check['final_rank_mod_q'] == 39
        assert 'AssertionError' in old_err.read_text()
        assert 'Build completed successfully' in build and f'RankPrefixP{p}.' in build
        assert '#print axioms' in module.read_text()
        assert not re.search(r'\b(sorry|admit|sorryAx|native_decide)\b', module.read_text())
        formal_case = next(x for x in FORMAL['cases'] if x['p'] == p)
        assert sha(result) == formal_case['prefix_result_sha256']
        assert sha(audit) == formal_case['prefix_audit_sha256']
        attempts.extend([
            {'p': p, 'stage': 'producer', 'exit_code': 0,
             'command': f'gtimeout 1800 ./sage -python experiments/hecke-d79-source-prefix-20261027/run.py --p {p}',
             'stdout_sha256': sha(HERE / f'p{p}-producer-stdout.txt'),
             'stderr_sha256': sha(HERE / f'p{p}-producer-stderr.txt'),
             'result_sha256': sha(result)},
            {'p': p, 'stage': 'audit_v1', 'exit_code': 1,
             'command': f'python3 experiments/hecke-d79-source-prefix-20261027/audit.py --p {p}',
             'stdout_sha256': sha(HERE / f'p{p}-audit-stdout.txt'),
             'stderr_sha256': sha(old_err), 'result_sha256': None},
            {'p': p, 'stage': 'audit_v2', 'exit_code': 0,
             'command': f'python3 experiments/hecke-d79-source-prefix-20261027/audit_v2.py --p {p}',
             'stdout_sha256': sha(HERE / f'p{p}-audit-v2-stdout.txt'),
             'stderr_sha256': sha(HERE / f'p{p}-audit-v2-stderr.txt'),
             'result_sha256': sha(audit)},
        ])
    receipt = {'schema': 'hecke-d79-source-prefix-attempts-v1', 'status': 'PASS',
               'sage_runtime_info_sha256': sha(HERE / 'sage-runtime-info.txt'),
               'lean_build_output_sha256': sha(HERE / 'formal/build-output.txt'),
               'attempts': attempts}
    (HERE / 'ATTEMPTS.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print('PREFIX_RECEIPTS_PASS', len(attempts))


if __name__ == '__main__':
    main()
