"""Read-only replay of N41 corrected suffix SAT receipts and formula hashes."""
import json
from pathlib import Path

from run import sha, status_from_output

HERE = Path(__file__).resolve().parent


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    audit_path = HERE / 'audit.json'
    audit = json.loads(audit_path.read_text())
    assert audit['protocol_sha256'] == sha(cfg_path)
    assert audit['status'] == 'PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT'
    arms = [('source_unpinned', cfg['sources']['source_formula']),
            ('guided_partial8_unpinned', cfg['sources']['guided_formula'])]
    statuses = {}
    for name, formula in arms:
        arm_dir = HERE / 'arms' / name
        if not arm_dir.exists():
            statuses[name] = 'NOT_RUN'
            continue
        receipt = json.loads((arm_dir / 'receipt.json').read_text())
        stdout, stderr = arm_dir / 'stdout.txt', arm_dir / 'stderr.txt'
        assert receipt['protocol_sha256'] == sha(cfg_path)
        assert receipt['audit_sha256'] == sha(audit_path)
        assert receipt['formula_sha256'] == formula['sha256']
        assert receipt['stdout_sha256'] == sha(stdout)
        assert receipt['stderr_sha256'] == sha(stderr)
        assert receipt['command'] == ([cfg['sources']['solver']['path']] +
                                      cfg['solver_flags'] + [formula['path']])
        assert receipt['status'] == status_from_output(stdout.read_text(errors='replace'),
                                                       receipt['exit_code'], receipt['stop_reason'])
        assert receipt['sampled_peak_combined_rss_bytes'] <= cfg['rss_cap_bytes'] or receipt['stop_reason'] == 'RSS_CAP'
        statuses[name] = receipt['status']
    print(json.dumps({'status': 'REPLAY_PASS', 'arms': statuses}, sort_keys=True))


if __name__ == '__main__':
    main()
