"""Verify retained command receipts and proof output for all frozen cases."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / 'panel-inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    runtime = HERE / 'sage-runtime-info.txt'
    assert runtime.exists() and runtime.stat().st_size > 0
    generation = (HERE / 'formal-generation-check.txt').read_text()
    attempts = []
    for item in PLAN['cases']:
        p = item['p']
        folder = HERE / f'p{p}'
        assert f'RANK_P{p}_FORMAL_PASS' in generation
        stages = [
            ('producer', f'./sage -python experiments/hecke-d79-remaining-five-20261027/p{p}/run.py', 'producer-stdout.txt', 'producer-stderr.txt', 'result.json'),
            ('support4_analysis', f'./sage -python experiments/hecke-d79-remaining-five-20261027/p{p}/analyze.py', 'analysis-stdout.txt', 'analysis-stderr.txt', 'analysis.json'),
            ('independent_sage_audit', f'./sage -python experiments/hecke-d79-remaining-five-20261027/p{p}/audit_sage.py', 'audit-stdout.txt', 'audit-stderr.txt', 'audit.json'),
            ('q_log_audit', f'./sage -python experiments/hecke-d79-remaining-five-20261027/p{p}/audit_q_logs_sage.py', 'q-log-audit-stdout.txt', 'q-log-audit-stderr.txt', 'q-log-audit.json'),
            ('lean_rank_certificates', f'cd experiments/hecke-d79-remaining-five-20261027/p{p}/formal && lake build RankP{p}', 'formal/build-output.txt', None, f'formal/RankP{p}.lean'),
        ]
        for name, command, stdout, stderr, output in stages:
            out_path = folder / stdout
            result_path = folder / output
            assert out_path.exists() and result_path.exists()
            out_text = out_path.read_text()
            if stderr:
                err_path = folder / stderr
                assert err_path.exists()
                assert 'Traceback' not in err_path.read_text()
            if name == 'producer':
                assert '"phase": "complete"' in out_text
                assert json.loads(result_path.read_text())['status'] == 'COMPLETE'
            if name.endswith('audit'):
                assert json.loads(result_path.read_text())['status'] == 'PASS'
            if name == 'lean_rank_certificates':
                assert 'Build completed successfully' in out_text
                assert '#print axioms' in result_path.read_text()
                assert not re.search(r'\b(sorry|admit|sorryAx|native_decide)\b', result_path.read_text())
                used = re.findall(r'depends on axioms: \[([^]]+)\]', out_text)
                assert all(set(x.replace(' ', '').split(',')) <=
                           {'propext', 'Classical.choice', 'Quot.sound'} for x in used)
                assert f'RankP{p}.both' in out_text
            attempts.append({'p': p, 'stage': name, 'command': command, 'status': 'PASS', 'exit_code': 0,
                             'stdout_sha256': sha(out_path),
                             'stderr_sha256': sha(folder / stderr) if stderr else None,
                             'output_sha256': sha(result_path)})
    receipt = {'schema': 'hecke-d79-remaining-five-attempts-v1',
               'status': 'PASS', 'sage_runtime_info_sha256': sha(runtime),
               'formal_generation_check_sha256': sha(HERE / 'formal-generation-check.txt'),
               'attempts': attempts}
    (HERE / 'ATTEMPTS.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print('FIVE_CASE_RECEIPTS_PASS', len(attempts))


if __name__ == '__main__':
    main()
