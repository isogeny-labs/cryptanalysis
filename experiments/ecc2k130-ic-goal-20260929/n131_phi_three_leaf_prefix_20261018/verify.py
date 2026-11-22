"""Read-only replay of source, query, monitor, and solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def query_sha(original, units):
    if not units:
        return sha(original)
    digest = hashlib.sha256()
    with original.open('rb') as source:
        header = source.readline().decode('ascii').split()
        assert header[:2] == ['p', 'cnf'] and len(header) == 4
        digest.update(('p cnf %s %d\n' % (header[2], int(header[3]) + len(units))).encode())
        while True:
            block = source.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    for literal in units:
        digest.update(('%d 0\n' % literal).encode())
    return digest.hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = load(cfg_path)
    assert cfg['status'] == 'FROZEN_BEFORE_SOLVER'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    mapping = load(HERE / 'mapping_audit.json')
    assert mapping['status'] == 'PASS_EXACT_FORMULA_AND_LEAF_VARIABLE_MAP'
    assert mapping['protocol_sha256'] == sha(cfg_path)
    for i in range(3):
        assert mapping['leaf_map'][str(i)] == list(range(2 + 10 * i, 12 + 10 * i))
    first = load(HERE / 'attempt1_failure.json')
    assert first['status'] == 'PRODUCER_FAILURE_MONITOR_PERMISSION'
    assert first['exact_parent_wall_seconds'] is None
    assert first['protocol_sha256'] == sha(cfg_path)
    assert first['stdout_sha256'] == sha(HERE / 'attempt1_failed_arms/baseline/stdout.txt')
    assert first['stderr_sha256'] == sha(HERE / 'attempt1_failed_arms/baseline/stderr.txt')
    original = Path(cfg['sources']['formula']['path'])
    names = [('baseline', None), ('invalid', cfg['invalid_domain_control'])]
    names += [('ordinary_%02d' % i, row) for i, row in enumerate(cfg['ordinary_prefixes'])]
    statuses = {}
    max_rss = 0
    total_wall = 0.0
    search_arms = []
    for name, codes in names:
        arm = HERE / 'arms' / name
        receipt = load(arm / 'receipt.json')
        assert receipt['arm'] == name and receipt['codes'] == codes
        assert receipt['protocol_sha256'] == sha(cfg_path)
        assert receipt['stdout_sha256'] == sha(arm / 'stdout.txt')
        assert receipt['stderr_sha256'] == sha(arm / 'stderr.txt')
        units = [] if codes is None else [
            (2 + 10 * pos + bit) * (1 if code >> bit & 1 else -1)
            for pos, code in enumerate(codes) for bit in range(10)]
        assert receipt['units'] == units
        assert receipt['query_sha256'] == query_sha(original, units)
        assert receipt['wall_seconds'] <= cfg['per_arm_parent_wall_cap_seconds'] + 1
        assert receipt['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
        max_rss = max(max_rss, receipt['sampled_peak_combined_rss_bytes'])
        total_wall += receipt['wall_seconds']
        stdout = (arm / 'stdout.txt').read_text(errors='replace')
        if name == 'invalid':
            assert receipt['status'] == 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT'
            assert 's UNSATISFIABLE' in stdout
        else:
            assert receipt['status'] == 'BOUNDED_UNKNOWN_ARM_WALL_CAP'
            assert receipt['stop_reason'] == 'ARM_WALL_CAP'
            assert not any(line.startswith(('s SATISFIABLE', 's UNSATISFIABLE'))
                           for line in stdout.splitlines())
        restarts = stdout.count('c rst ')
        if restarts:
            search_arms.append(name)
        statuses[name] = receipt['status']
    assert total_wall < cfg['campaign_parent_wall_cap_seconds']
    assert len(cfg['ordinary_prefixes']) == 16
    print(json.dumps({'status': 'PASS_FROZEN_PREFIX_PANEL_RECEIPTS',
                      'ordinary_capped': 16, 'invalid_control': statuses['invalid'],
                      'arms_with_restart_logs': search_arms,
                      'sum_arm_wall_seconds': total_wall,
                      'max_sampled_combined_rss_bytes': max_rss}, sort_keys=True))


if __name__ == '__main__':
    main()
