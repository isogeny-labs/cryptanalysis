"""Monitored one-worker target-conditioned two-plus-one join."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_PUBLIC_JOIN'
    for name, digest in protocol['source_sha256'].items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        assert sha(path) == digest, name
    command = [str(HERE / 'join_2p1'), str(HERE / 'join_input.tsv')]
    stdout_path, stderr_path = HERE / 'join.stdout', HERE / 'join.stderr'
    peak = 0
    stop_reason = None
    monitor_error = None
    start = time.monotonic_ns()
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        worker = psutil.Process(process.pid)
        parent = psutil.Process()
        while process.poll() is None:
            try:
                peak = max(peak, worker.memory_info().rss + parent.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
                if process.poll() is None:
                    monitor_error = type(exc).__name__
                    stop_reason = 'MONITOR_FAILURE'
                    break
            if peak > protocol['combined_rss_cap_bytes']:
                stop_reason = 'RSS_CAP'
            elif (time.monotonic_ns() - start) / 1e9 > protocol['parent_wall_cap_seconds']:
                stop_reason = 'PARENT_WALL_CAP'
            if stop_reason:
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    elapsed = (time.monotonic_ns() - start) / 1e9
    lines = stdout_path.read_text().splitlines()
    hits = [line for line in lines if line.startswith('HIT ')]
    misses = [line for line in lines if line.startswith('MISS_COMPLETE ')]
    if stop_reason:
        status = 'BOUNDED_UNKNOWN'
    elif exit_code == 0 and len(hits) == 1:
        status = 'HIT_PENDING_SAGE_REPLAY'
    elif exit_code == 0 and len(misses) == 1:
        status = 'COMPLETE_MISS'
    else:
        status = 'PRODUCER_FAILURE'
    result = {'status': status, 'command': command,
              'protocol_sha256': sha(protocol_path), 'exit_code': exit_code,
              'stop_reason': stop_reason, 'monitor_error': monitor_error,
              'parent_wall_seconds': elapsed,
              'sampled_peak_combined_rss_bytes': peak,
              'hit_lines': hits, 'miss_lines': misses,
              'orientation_done_lines': [line for line in lines if line.startswith('ORIENTATION_DONE ')],
              'left2_done_lines': [line for line in lines if line.startswith('LEFT2_DONE ')],
              'right2_done_lines': [line for line in lines if line.startswith('RIGHT2_DONE ')],
              'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
    with (HERE / 'run_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
