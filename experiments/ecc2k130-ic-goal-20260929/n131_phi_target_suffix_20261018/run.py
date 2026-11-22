"""Bounded target-conditioned joint prefix/suffix SAT panel."""
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


def bits(value, variables):
    return [v if value >> i & 1 else -v for i, v in enumerate(variables)]


def units_for(cfg, branch):
    suffix = [lit for i, code in enumerate(cfg['suffix_codes'])
              for lit in bits(code, list(range(122 + 10 * i, 132 + 10 * i)))]
    if branch is None:
        assert len(suffix) == 30
        return suffix
    prefix = [lit for i, code in enumerate(cfg['prefix_codes'])
              for lit in bits(code, list(range(2 + 10 * i, 12 + 10 * i)))]
    forward = [lit for i, mask in enumerate(cfg['prefix_partial_phi_masks'])
               for lit in bits(mask, list(range(152 + 131 * i, 283 + 131 * i)))]
    backward = [lit for i, mask in enumerate(branch['partial_phi_masks'])
                for lit in bits(mask, list(range(152 + 131 * (10 + i),
                                               283 + 131 * (10 + i))))]
    selector = bits(branch['endpoint_selector'], [1855, 1856])
    units = prefix + suffix + forward + backward + selector
    assert len(units) == 717 and len({abs(x) for x in units}) == 717
    return units


def query_from_units(source, destination, units):
    with Path(source).open('rb') as src, destination.open('xb') as out:
        header = src.readline().decode('ascii').split()
        assert header[:2] == ['p', 'cnf'] and len(header) == 4
        out.write(('p cnf %s %d\n' % (header[2], int(header[3]) + len(units))).encode())
        while block := src.read(1024 * 1024):
            out.write(block)
        for lit in units:
            out.write(('%d 0\n' % lit).encode())


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
    if exit_code == 15 and 'Total time (this thread)' in output:
        return 'BOUNDED_UNKNOWN_SOLVER_TIME_LIMIT_NO_TERMINAL'
    return 'PRODUCER_FAILURE_NO_TERMINAL_STATE'


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SOLVER'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    original = Path(cfg['sources']['formula']['path'])
    solver = cfg['sources']['solver']['path']
    arms = [('suffix_code_only', None), ('invalid_partial12_bit0', cfg['invalid_control'])]
    arms += [('endpoint_%d_orientation_%d' % (b['endpoint_selector'], b['endpoint_orientation']), b)
             for b in cfg['branches']]
    campaign_start = time.monotonic()
    for name, branch in arms:
        arm_dir = HERE / 'arms' / name
        arm_dir.mkdir(parents=True, exist_ok=False)
        units = units_for(cfg, branch)
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
        receipt = {'arm': name, 'branch': branch, 'units': units,
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
        if name == 'invalid_partial12_bit0' and receipt['status'] != 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT':
            break
        if stop_reason in ('RSS_CAP', 'CAMPAIGN_WALL_CAP'):
            break


if __name__ == '__main__':
    main()
