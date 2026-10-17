"""Bounded, one-worker N41 search on the second raw lift."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'n41_raw1_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_N41_RAW1_QUERY'
    paths = {'input': HERE / 'n41_raw1_join_input.tsv',
             'lift_targets': HERE / 'lift_targets.json',
             'native_binary': SOURCE / 'join_orbit',
             'native_source': SOURCE / 'join_orbit.cpp',
             'states': SOURCE / 'n41_states.json',
             'runtime': HERE / 'sage_runtime_info.json'}
    for name, path in paths.items():
        assert sha(path) == protocol['source_sha256'][name], name
    assert protocol['worker_count'] == 1
    command = [str(paths['native_binary']), str(paths['input'])]
    start = time.monotonic_ns()
    peak = 0
    stop_reason = None
    stdout_path, stderr_path = HERE / 'n41_raw1.stdout', HERE / 'n41_raw1.stderr'
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        worker = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak = max(peak, worker.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > protocol['worker_rss_cap_bytes']:
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
              'stop_reason': stop_reason, 'parent_wall_seconds': elapsed,
              'sampled_peak_worker_rss_bytes': peak,
              'hit_lines': hits, 'miss_lines': misses,
              'orientation_done_lines': [line for line in lines if line.startswith('ORIENTATION_DONE ')],
              'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
    with (HERE / 'n41_raw1_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
