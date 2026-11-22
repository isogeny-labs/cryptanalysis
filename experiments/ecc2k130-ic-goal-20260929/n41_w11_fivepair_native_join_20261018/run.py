"""Run one frozen, resource-capped unpinned five-pair public query."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'query_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
outcome = HERE / 'query_result.json'
assert not outcome.exists()
command = [str(HERE / 'join'), str(HERE / 'join_input.tsv'),
           str(protocol['query_seed']), str(protocol['max_probes'])]
started = time.monotonic()
parent = psutil.Process(os.getpid())
peak = 0
samples = 0
stop = None
monitor_error = None
stdout = HERE / 'join.stdout'
stderr = HERE / 'join.stderr'
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > protocol['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic() - started > protocol['parent_wall_cap_seconds']:
            stop = 'WALL_CAP'
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    exit_code = child.wait()
stream = stdout.read_text(errors='replace')
lines = stream.splitlines()
stage_lines = [line for line in lines if line.startswith(('CHECK_PASS ',
                                                         'RIGHT_TABLE ',
                                                         'LEFT_TABLE '))]
hits = [line for line in lines if line.startswith('HIT ')]
misses = [line for line in lines if line.startswith('NO_HIT ')]
if stop == 'WALL_CAP':
    status = 'BOUNDED_UNKNOWN'
elif stop:
    status = stop
elif exit_code != 0:
    status = 'PRODUCER_FAILURE_NATIVE'
elif len(hits) == 1 and len(misses) == 0 and len(stage_lines) == 3:
    status = 'N41_W11_NATIVE_RELATION_UNVERIFIED'
elif len(misses) == 1 and len(hits) == 0 and len(stage_lines) == 3:
    status = 'BOUNDED_UNKNOWN_SEARCH_CAP'
else:
    status = 'PRODUCER_FAILURE_NO_TERMINAL_STATUS'
hit = None
if hits:
    tokens = hits[0].split()
    assert len(tokens) == 11
    hit = {'state_ids': [int(x) for x in tokens[1:6]],
           'probes': int(tokens[6]), 'hash_hits': int(tokens[7]),
           'rejected_hit_or_probe': int(tokens[8]),
           'online_query_seconds': float(tokens[9]),
           'native_total_seconds': float(tokens[10])}
result = {'status': status, 'candidate_id': None,
          'curve_id': protocol['curve_id'], 'command': command,
          'stop_reason': stop, 'monitor_error': monitor_error,
          'worker_count': 1, 'exit_code': exit_code,
          'stage_lines': stage_lines, 'hit': hit,
          'parent_wall_seconds': time.monotonic() - started,
          'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
          'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
          'protocol_sha256': sha(HERE / 'query_protocol.json')}
outcome.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'hit', 'parent_wall_seconds',
                   'sampled_peak_combined_rss_bytes')}, sort_keys=True))
