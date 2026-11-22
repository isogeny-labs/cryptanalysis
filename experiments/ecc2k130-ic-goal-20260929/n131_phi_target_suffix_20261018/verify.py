"""Read-only replay of exact suffix and joint end-cut query receipts."""
import hashlib
import json
from pathlib import Path

from run import sha, status_from_output, units_for

HERE = Path(__file__).resolve().parent


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    arms = [('suffix_code_only', None), ('invalid_partial12_bit0', cfg['invalid_control'])]
    arms += [('endpoint_%d_orientation_%d' % (b['endpoint_selector'], b['endpoint_orientation']), b)
             for b in cfg['branches']]
    statuses = {}
    for name, branch in arms:
        path = HERE / 'arms' / name
        if not path.exists():
            statuses[name] = 'NOT_RUN'
            continue
        receipt = json.loads((path / 'receipt.json').read_text())
        assert receipt['protocol_sha256'] == sha(cfg_path)
        assert receipt['branch'] == branch
        units = units_for(cfg, branch)
        assert receipt['units'] == units
        h = hashlib.sha256()
        with Path(cfg['sources']['formula']['path']).open('rb') as src:
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
