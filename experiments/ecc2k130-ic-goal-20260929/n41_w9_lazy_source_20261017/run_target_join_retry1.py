"""Frozen one-worker target-conditioned W9 orbit join with resource monitor."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017'
SOURCE = PRIOR / 'join_input.tsv'
BINARY = HERE / 'join_target_conditioned'
CAP_SECONDS = 600
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


fixture = json.loads((HERE / 'fixture.json').read_text())
header = SOURCE.open().readline().split()
assert header[:3] == ['ECC2K41', '5', '284']
assert list(map(int, header[3:5])) == fixture['original_raw_point']
protocol = {'status': 'FROZEN_BEFORE_TARGET_CONDITIONED_JOIN',
            'curve_id': fixture['curve_id'],
            'target_raw_point': fixture['original_raw_point'],
            'source_rule': 'five W9 signed-pair lists; 2+1+2 exact target-conditioned group lookup; all 41 Frobenius orientations',
            'worker_count': 1, 'parent_wall_cap_seconds': CAP_SECONDS,
            'worker_rss_cap_bytes': RSS_CAP,
            'compiler_command': ['clang++', '-O3', '-std=c++20', '-DNDEBUG',
                                 'join_target_conditioned.cpp', '-o', 'join_target_conditioned'],
            'source_sha256': {'input': sha(SOURCE), 'source': sha(HERE / 'join_target_conditioned.cpp'),
                              'binary': sha(BINARY), 'fixture': sha(HERE / 'fixture.json'),
                              'runner': sha(Path(__file__))}}
protocol_path = HERE / 'target_join_protocol_retry1.json'
with protocol_path.open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
command = [str(BINARY), str(SOURCE)]
stdout_path, stderr_path = HERE / 'target_join_retry1.stdout', HERE / 'target_join_retry1.stderr'
start = time.monotonic_ns()
peak = 0
stop = None
with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    worker = psutil.Process(process.pid)
    while process.poll() is None:
        try:
            peak = max(peak, worker.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            if process.poll() is None:
                stop = 'MONITOR_FAILURE'
                process.kill()
            break
        if peak > RSS_CAP:
            stop = 'RSS_CAP'
            process.kill()
            break
        if (time.monotonic_ns() - start) / 1e9 > CAP_SECONDS:
            stop = 'PARENT_WALL_CAP'
            process.kill()
            break
        time.sleep(0.05)
    exit_code = process.wait()
elapsed = time.monotonic_ns() - start
lines = stdout_path.read_text(errors='replace').splitlines()
hits = [line for line in lines if line.startswith('HIT ')]
misses = [line for line in lines if line.startswith('MISS_COMPLETE ')]
if stop:
    status = 'BOUNDED_UNKNOWN' if stop != 'MONITOR_FAILURE' else stop
elif exit_code == 0 and len(hits) == 1:
    status = 'HIT_PENDING_SAGE_REPLAY'
elif exit_code == 0 and len(misses) == 1:
    status = 'COMPLETE_MISS'
else:
    status = 'PRODUCER_FAILURE'
result = {'status': status, 'command': command,
          'protocol_sha256': sha(protocol_path), 'exit_code': exit_code,
          'stop_reason': stop, 'parent_wall_ns': elapsed,
          'sampled_peak_worker_rss_bytes': peak,
          'left_done': [line for line in lines if line.startswith('LEFT_DONE ')],
          'right_done': [line for line in lines if line.startswith('RIGHT_DONE ')],
          'orientation_done': [line for line in lines if line.startswith('ORIENTATION_DONE ')],
          'hits': hits, 'misses': misses,
          'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
with (HERE / 'target_join_result_retry1.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': status, 'parent_wall_seconds': elapsed / 1e9,
                  'sampled_peak_worker_rss_bytes': peak,
                  'hit_lines': hits}), flush=True)
