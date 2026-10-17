"""Audit the matched W23 matrix-policy conflict screen."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((BASE / 'matrix_protocol.json').read_text())
    result = json.loads((BASE / 'matrix_result.json').read_text())
    assert protocol['status'] == 'FROZEN_W23_MATRIX_POLICY_CONFLICT_SCREEN'
    assert protocol['source_sha256'] == {
        'script': sha(BASE / 'matrix_probe.py'),
        'formula': sha(BASE / 'ordinary.xcnf'),
        'solver': sha(Path('/opt/homebrew/bin/cryptominisat5')),
        'public_query': sha(BASE / 'result.json')}
    assert result['source_sha256'] == protocol['source_sha256']
    assert result['protocol_sha256'] == sha(BASE / 'matrix_protocol.json')
    assert result['status'] == 'COMPLETE_MATRIX_POLICY_SCREEN'
    assert [arm['name'] for arm in result['arms']] == ['default', 'wide']
    summary = []
    for arm in result['arms']:
        name = arm['name']
        stdout = BASE / f'matrix_{name}.stdout'
        stderr = BASE / f'matrix_{name}.stderr'
        assert arm['stdout_sha256'] == sha(stdout)
        assert arm['stderr_sha256'] == sha(stderr)
        assert stderr.stat().st_size == 0
        raw = stdout.read_text(errors='replace')
        rows = [line for line in raw.splitlines() if line.startswith('c rst')]
        matrix = [line for line in raw.splitlines()
                  if '[matrix]' in line or 'Using ' in line and 'matrices' in line]
        assert len(rows) == arm['restart_count'] == 336
        assert (rows[0], rows[-1]) == (arm['first_restart'], arm['last_restart'])
        assert matrix == arm['matrix_lines']
        assert arm['command'] == [
            '/opt/homebrew/bin/cryptominisat5', *protocol['shared_flags'],
            *(protocol['wide_flags'] if name == 'wide' else []),
            str(BASE / 'ordinary.xcnf')]
        assert arm['status_lines'] == ['s INDETERMINATE']
        assert arm['stop_reason'] is None and arm['exit_code'] == 0
        assert arm['sampled_peak_combined_rss_bytes'] <= 4294967296
        assert arm['elapsed_ns'] < 110_000_000_000
        assert rows[-1].split()[6] == '100K'
        free = int(rows[-1].split()[7])
        assert free == 124469
        admitted = [int(line.split('Using ')[1].split(' matrices')[0])
                    for line in matrix if 'Using ' in line and ' matrices' in line]
        assert admitted and all(value == (0 if name == 'default' else 10)
                                for value in admitted)
        summary.append({'arm': name, 'final_free_variables': free,
                        'matrix_admissions': admitted,
                        'elapsed_ns': arm['elapsed_ns'],
                        'sampled_peak_combined_rss_bytes':
                        arm['sampled_peak_combined_rss_bytes']})
    report = {'status': 'PASS_W23_MATRIX_POLICY_RECEIPT_AUDIT',
              'same_conflict_boundary': 100000,
              'same_final_free_variables': 124469,
              'arms': summary,
              'protocol_sha256': sha(BASE / 'matrix_protocol.json'),
              'result_sha256': sha(BASE / 'matrix_result.json')}
    with (BASE / 'matrix_audit_result.json').open('x') as out:
        json.dump(report, out, sort_keys=True, indent=2)
        out.write('\n')
    print(report['status'], [(r['arm'], r['matrix_admissions'][0]) for r in summary])


if __name__ == '__main__':
    main()
