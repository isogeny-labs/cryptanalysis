"""Bounded, receipt-preserving official-Q three-leaf prefix SAT panel."""
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
    try:
        raw = subprocess.check_output(['ps', '-o', 'rss=', '-p', str(pid)],
                                      stderr=subprocess.DEVNULL, timeout=1).strip()
        return int(raw) * 1024 if raw else 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
        return 0


def query_from_units(source, destination, units):
    with Path(source).open('rb') as source_file, destination.open('xb') as out:
        header = source_file.readline().decode('ascii').split()
        assert header[:2] == ['p', 'cnf'] and len(header) == 4
        out.write(('p cnf %s %d\n' % (header[2], int(header[3]) + len(units))).encode())
        while True:
            block = source_file.read(1024 * 1024)
            if not block:
                break
            out.write(block)
        for literal in units:
            out.write(('%d 0\n' % literal).encode())


def status_from_output(output, exit_code, stop_reason):
    if stop_reason:
        return 'BOUNDED_UNKNOWN_' + stop_reason
    lines = output.splitlines()
    states = [line.strip() for line in lines if line.startswith('s ')]
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
    campaign_start = time.monotonic()
    arms = [('baseline', None), ('invalid', cfg['invalid_domain_control'])]
    arms += [('ordinary_%02d' % i, codes) for i, codes in enumerate(cfg['ordinary_prefixes'])]
    for name, codes in arms:
        arm_dir = HERE / 'arms' / name
        arm_dir.mkdir(parents=True, exist_ok=False)
        units = []
        if codes is not None:
            assert len(codes) == 3
            units = [(2 + 10 * position + bit) * (1 if (code >> bit) & 1 else -1)
                     for position, code in enumerate(codes) for bit in range(10)]
        query = arm_dir / 'query.xcnf'
        if units:
            query_from_units(original, query, units)
            query_path = query
        else:
            query_path = original
        command = [solver] + cfg['solver_flags'] + [str(query_path)]
        stdout_path = arm_dir / 'stdout.txt'
        stderr_path = arm_dir / 'stderr.txt'
        stop_reason = None
        peak = 0
        start = time.monotonic()
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                       start_new_session=True)
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
            exit_code = process.wait()
        output = stdout_path.read_text(errors='replace')
        receipt = {'arm': name, 'codes': codes, 'units': units,
                   'status': status_from_output(output, exit_code, stop_reason),
                   'stop_reason': stop_reason, 'exit_code': exit_code,
                   'command': command,
                   'query_sha256': sha(query_path),
                   'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path),
                   'wall_seconds': time.monotonic() - start,
                   'sampled_peak_combined_rss_bytes': peak,
                   'protocol_sha256': sha(cfg_path)}
        with (arm_dir / 'receipt.json').open('x') as handle:
            json.dump(receipt, handle, sort_keys=True, indent=2)
            handle.write('\n')
        print(json.dumps({key: receipt[key] for key in ('arm', 'status', 'wall_seconds',
                                                      'sampled_peak_combined_rss_bytes')},
                         sort_keys=True), flush=True)
        # Unit-augmented queries are deterministic derivatives of the frozen
        # source and units in each receipt; retain hashes, logs and receipts.
        if units:
            query.unlink()
        if name == 'invalid' and receipt['status'] != 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT':
            break
        if stop_reason in ('RSS_CAP', 'CAMPAIGN_WALL_CAP'):
            break


if __name__ == '__main__':
    main()
