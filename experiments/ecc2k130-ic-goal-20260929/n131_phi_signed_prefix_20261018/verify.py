"""Read-only verification of frozen signed-prefix arm receipts."""
import hashlib
import json
from pathlib import Path

from run import sha, status_from_output, units_for

HERE = Path(__file__).resolve().parent


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SOLVER'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    assert len(cfg['branches']) == 8
    assert len({tuple(b['signs']) for b in cfg['branches']}) == 8
    arms = [('invalid_partial0_bit0', cfg['invalid_control'])]
    arms += [('sign_%d%d%d' % tuple(b['signs']), b) for b in cfg['branches']]
    statuses = {}
    for name, branch in arms:
        path = HERE / 'arms' / name
        if not path.exists():
            statuses[name] = 'NOT_RUN'
            continue
        receipt = json.loads((path / 'receipt.json').read_text())
        assert receipt['protocol_sha256'] == sha(cfg_path)
        assert receipt['codes'] == cfg['codes']
        assert receipt['signs'] == branch['signs']
        assert receipt['partial_phi_masks'] == branch['partial_phi_masks']
        units = units_for(cfg, branch['partial_phi_masks'])
        assert receipt['units'] == units
        h = hashlib.sha256()
        source = Path(cfg['sources']['formula']['path'])
        with source.open('rb') as src:
            header = src.readline().decode('ascii').split()
            h.update(('p cnf %s %d\n' % (header[2], int(header[3]) + len(units))).encode())
            while block := src.read(1024 * 1024):
                h.update(block)
        for lit in units:
            h.update(('%d 0\n' % lit).encode())
        assert receipt['query_sha256'] == h.hexdigest()
        assert receipt['stdout_sha256'] == sha(path / 'stdout.txt')
        assert receipt['stderr_sha256'] == sha(path / 'stderr.txt')
        assert receipt['command'] == [cfg['sources']['solver']['path']] + cfg['solver_flags'] + [str(path / 'query.xcnf')]
        assert receipt['status'] == status_from_output((path / 'stdout.txt').read_text(errors='replace'),
                                                       receipt['exit_code'], receipt['stop_reason'])
        assert receipt['sampled_peak_combined_rss_bytes'] <= cfg['rss_cap_bytes'] or receipt['stop_reason'] == 'RSS_CAP'
        statuses[name] = receipt['status']
    print(json.dumps({'status': 'REPLAY_PASS', 'arms': statuses}, sort_keys=True))


if __name__ == '__main__':
    main()
