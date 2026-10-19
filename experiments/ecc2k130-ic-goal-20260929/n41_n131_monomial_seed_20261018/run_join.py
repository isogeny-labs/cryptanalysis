"""Monitor exact N41 five-pair join on monomial-halftrace source."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg_path = HERE / 'join_protocol.json'
cfg = json.loads(cfg_path.read_text())
assert cfg['status'] == 'FROZEN_BEFORE_JOIN'
for name, entry in cfg['sources'].items():
    assert sha(entry['path']) == entry['sha256'], name
command = [cfg['sources']['binary']['path'], cfg['sources']['input']['path']]
started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
with (HERE / 'join.stdout').open('x') as stdout, (HERE / 'join.stderr').open('x') as stderr:
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    worker, parent = psutil.Process(process.pid), psutil.Process()
    while process.poll() is None:
        try:
            peak = max(peak, worker.memory_info().rss + parent.memory_info().rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if process.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                process.kill()
                break
        if peak > cfg['combined_rss_cap_bytes']:
            stop = 'RSS_CAP'
        elif time.monotonic() - started >= cfg['parent_wall_cap_seconds']:
            stop = 'PARENT_WALL_CAP'
        if stop:
            process.kill()
            break
        time.sleep(0.05)
    exit_code = process.wait()
lines = (HERE / 'join.stdout').read_text().splitlines()
hits = [line for line in lines if line.startswith('HIT ')]
done = [line for line in lines if line.startswith('ORIENTATION_DONE ')]
misses = [line for line in lines if line.startswith('MISS_COMPLETE ')]
status = ('BOUNDED_UNKNOWN' if stop else
          'HIT_PENDING_SAGE_REPLAY' if exit_code == 0 and len(hits) == 1 else
          'COMPLETE_MISS' if exit_code == 0 and len(misses) == 1 else
          'PRODUCER_FAILURE')
result = {'status':status,'candidate_id':None,'curve_id':cfg['curve_id'],
          'command':command,'exit_code':exit_code,'stop_reason':stop,
          'monitor_error':monitor_error,'rss_samples':samples,
          'sampled_peak_combined_rss_bytes':peak,
          'parent_wall_seconds':time.monotonic()-started,
          'hit_lines':hits,'orientation_done_lines':done,'miss_lines':misses,
          'protocol_sha256':sha(cfg_path),'stdout_sha256':sha(HERE/'join.stdout'),
          'stderr_sha256':sha(HERE/'join.stderr')}
(HERE/'join_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','parent_wall_seconds','sampled_peak_combined_rss_bytes','hit_lines','stop_reason')},sort_keys=True),flush=True)
