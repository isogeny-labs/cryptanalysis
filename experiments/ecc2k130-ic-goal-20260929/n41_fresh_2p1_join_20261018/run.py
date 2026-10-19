"""Bounded fresh-public-point N41 two-plus-one indexed join."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_FRESH_JOIN'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    command = [cfg['sources']['binary']['path'], str(HERE / 'join_input.tsv')]
    peak = 0
    samples = 0
    stop_reason = None
    monitor_error = None
    started = time.monotonic()
    with (HERE / 'join.stdout').open('x') as stdout, (HERE / 'join.stderr').open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        worker = psutil.Process(process.pid)
        parent = psutil.Process()
        while process.poll() is None:
            try:
                peak = max(peak, worker.memory_info().rss + parent.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
                if process.poll() is None:
                    monitor_error = type(exc).__name__
                    stop_reason = 'MONITOR_FAILURE'
                    break
            if peak > cfg['combined_rss_cap_bytes']:
                stop_reason = 'RSS_CAP'
            elif time.monotonic() - started >= cfg['parent_wall_cap_seconds']:
                stop_reason = 'PARENT_WALL_CAP'
            if stop_reason:
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    lines = (HERE / 'join.stdout').read_text().splitlines()
    hits = [line for line in lines if line.startswith('HIT ')]
    done = [line for line in lines if line.startswith('ORIENTATION_DONE ')]
    misses = [line for line in lines if line.startswith('MISS_COMPLETE ')]
    if stop_reason:
        status = 'BOUNDED_UNKNOWN'
    elif exit_code == 0 and len(hits) == 1:
        status = 'HIT_PENDING_SAGE_REPLAY'
    elif exit_code == 0 and len(misses) == 1:
        status = 'COMPLETE_MISS'
    else:
        status = 'PRODUCER_FAILURE'
    result = {
        'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
        'command': command, 'exit_code': exit_code, 'stop_reason': stop_reason,
        'monitor_error': monitor_error, 'rss_samples': samples,
        'sampled_peak_combined_rss_bytes': peak,
        'parent_wall_seconds': time.monotonic() - started,
        'protocol_sha256': sha(cfg_path), 'stdout_sha256': sha(HERE / 'join.stdout'),
        'stderr_sha256': sha(HERE / 'join.stderr'),
        'hit_lines': hits, 'orientation_done_lines': done, 'miss_lines': misses,
    }
    (HERE / 'run_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
