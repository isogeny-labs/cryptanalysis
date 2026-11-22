"""Read-only replay of frozen dual-end public-point query receipt."""
import json
from pathlib import Path

from run import sha, status_from_output

HERE = Path(__file__).resolve().parent


def main():
    cfg_path, audit_path, receipt_path = (HERE / name for name in
                                         ('protocol.json', 'audit.json', 'receipt.json'))
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    audit = json.loads(audit_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    assert audit['status'] == 'PASS_DUAL_END_GROUP_AND_XCNF_AUDIT'
    assert audit['protocol_sha256'] == sha(cfg_path)
    assert receipt['protocol_sha256'] == sha(cfg_path)
    assert receipt['audit_sha256'] == sha(audit_path)
    assert receipt['formula_sha256'] == cfg['sources']['dual_formula']['sha256']
    assert receipt['stdout_sha256'] == sha(HERE / 'stdout.txt')
    assert receipt['stderr_sha256'] == sha(HERE / 'stderr.txt')
    assert receipt['command'] == ([cfg['sources']['solver']['path']] +
                                  cfg['solver_flags'] + [cfg['sources']['dual_formula']['path']])
    assert receipt['status'] == status_from_output((HERE / 'stdout.txt').read_text(errors='replace'),
                                                   receipt['exit_code'], receipt['stop_reason'])
    assert receipt['sampled_peak_combined_rss_bytes'] <= cfg['rss_cap_bytes'] or receipt['stop_reason'] == 'RSS_CAP'
    print(json.dumps({'status': 'REPLAY_PASS', 'solver_status': receipt['status']}, sort_keys=True))


if __name__ == '__main__':
    main()
