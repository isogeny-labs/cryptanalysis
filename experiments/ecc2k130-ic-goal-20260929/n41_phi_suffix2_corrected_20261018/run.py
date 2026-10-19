"""Bounded paired unpinned N41 public-point solver run."""
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
    audit = json.loads((HERE / 'audit.json').read_text())
    assert audit['status'] == 'PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT'
    assert audit['protocol_sha256'] == sha(cfg_path)
    assert audit['guided_formula_sha256'] == cfg['sources']['guided_formula']['sha256']
    solver = cfg['sources']['solver']['path']
    arms = [('source_unpinned', cfg['sources']['source_formula']['path']),
            ('guided_partial8_unpinned', cfg['sources']['guided_formula']['path'])]
    campaign_start = time.monotonic()
    for name, formula in arms:
        arm_dir = HERE / 'arms' / name
        arm_dir.mkdir(parents=True, exist_ok=False)
        command = [solver] + cfg['solver_flags'] + [formula]
        stdout_path, stderr_path = arm_dir / 'stdout.txt', arm_dir / 'stderr.txt'
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
        receipt = {'arm': name, 'status': status_from_output(
                    stdout_path.read_text(errors='replace'), exit_code, stop_reason),
                   'stop_reason': stop_reason, 'exit_code': exit_code,
                   'command': command, 'formula_sha256': sha(formula),
                   'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path),
                   'wall_seconds': time.monotonic() - start,
                   'sampled_peak_combined_rss_bytes': peak,
                   'protocol_sha256': sha(cfg_path), 'audit_sha256': sha(HERE / 'audit.json')}
        with (arm_dir / 'receipt.json').open('x') as out:
            json.dump(receipt, out, sort_keys=True, indent=2)
            out.write('\n')
        print(json.dumps({key: receipt[key] for key in
                          ('arm', 'status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
                         sort_keys=True), flush=True)
        if stop_reason in ('RSS_CAP', 'CAMPAIGN_WALL_CAP'):
            break


if __name__ == '__main__':
    main()
