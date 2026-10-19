"""Bounded SAT panel for exact signed three-leaf partial-sum pins."""
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rss_bytes(pid):
    raw = subprocess.check_output(['ps', '-o', 'rss=', '-p', str(pid)], timeout=1).strip()
    return int(raw) * 1024 if raw else 0


def query_from_units(source, destination, units):
    with Path(source).open('rb') as src, destination.open('xb') as out:
        header = src.readline().decode('ascii').split()
        assert header[:2] == ['p', 'cnf'] and len(header) == 4
        out.write(('p cnf %s %d\n' % (header[2], int(header[3]) + len(units))).encode())
        while block := src.read(1024 * 1024):
            out.write(block)
        for lit in units:
            out.write(('%d 0\n' % lit).encode())


def units_for(cfg, masks):
    codes = cfg['codes']
    units = [(2 + 10 * i + j) * (1 if code >> j & 1 else -1)
             for i, code in enumerate(codes) for j in range(10)]
    units += [(152 + 131 * i + j) * (1 if mask >> j & 1 else -1)
              for i, mask in enumerate(masks) for j in range(131)]
    assert len(units) == 292
    return units


def status_from_output(output, exit_code, stop_reason):
    if stop_reason:
        return 'BOUNDED_UNKNOWN_' + stop_reason
    states = [line.strip() for line in output.splitlines() if line.startswith('s ')]
    if 's SATISFIABLE' in states:
        return 'SAT_REPORTED_NEEDS_INDEPENDENT_REPLAY'
    if 's UNSATISFIABLE' in states:
        return 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT'
    if 's UNKNOWN' in states:
        return 'BOUNDED_UNKNOWN_SOLVER'
    return 'PRODUCER_FAILURE_NO_TERMINAL_STATE' if exit_code is not None else 'PRODUCER_FAILURE'


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SOLVER'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    original = Path(cfg['sources']['formula']['path'])
    solver = cfg['sources']['solver']['path']
    arms = [('invalid_partial0_bit0', cfg['invalid_control'])]
    arms += [('sign_%d%d%d' % tuple(branch['signs']), branch)
             for branch in cfg['branches']]
    campaign_start = time.monotonic()
    for name, branch in arms:
        arm_dir = HERE / 'arms' / name
        arm_dir.mkdir(parents=True, exist_ok=False)
        units = units_for(cfg, branch['partial_phi_masks'])
        query = arm_dir / 'query.xcnf'
        query_from_units(original, query, units)
        command = [solver] + cfg['solver_flags'] + [str(query)]
        stdout_path = arm_dir / 'stdout.txt'
        stderr_path = arm_dir / 'stderr.txt'
        stop_reason = None
        peak = 0
        start = time.monotonic()
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            try:
                while process.poll() is None:
                    peak = max(peak, rss_bytes(process.pid) +
                               resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
                    if peak > cfg['rss_cap_bytes']:
                        stop_reason = 'RSS_CAP'
                    elif time.monotonic() - start > cfg['per_arm_parent_wall_cap_seconds']:
                        stop_reason = 'ARM_WALL_CAP'
                    elif time.monotonic() - campaign_start > cfg['campaign_parent_wall_cap_seconds']:
                        stop_reason = 'CAMPAIGN_WALL_CAP'
                    if stop_reason:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        break
                    time.sleep(0.1)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            exit_code = process.wait()
        receipt = {'arm': name, 'codes': cfg['codes'], 'signs': branch['signs'],
                   'partial_phi_masks': branch['partial_phi_masks'], 'units': units,
                   'status': status_from_output(stdout_path.read_text(errors='replace'),
                                                exit_code, stop_reason),
                   'stop_reason': stop_reason, 'exit_code': exit_code,
                   'command': command, 'query_sha256': sha(query),
                   'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path),
                   'wall_seconds': time.monotonic() - start,
                   'sampled_peak_combined_rss_bytes': peak,
                   'protocol_sha256': sha(cfg_path)}
        with (arm_dir / 'receipt.json').open('x') as out:
            json.dump(receipt, out, sort_keys=True, indent=2)
            out.write('\n')
        query.unlink()
        print(json.dumps({key: receipt[key] for key in
                          ('arm', 'status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                         sort_keys=True), flush=True)
        if name == 'invalid_partial0_bit0' and receipt['status'] != 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT':
            break
        if stop_reason in ('RSS_CAP', 'CAMPAIGN_WALL_CAP'):
            break


if __name__ == '__main__':
    main()
