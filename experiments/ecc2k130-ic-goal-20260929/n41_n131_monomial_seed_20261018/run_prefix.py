"""Monitor one native exact W29 prefix census under a frozen cap."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg_path = HERE / 'prefix_protocol.json'
cfg = json.loads(cfg_path.read_text())
assert cfg['status'] == 'FROZEN_BEFORE_PREFIX_CENSUS'
for name, entry in cfg['sources'].items():
    assert sha(entry['path']) == entry['sha256'], name
command = [cfg['sources']['binary']['path']]
start = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
with (HERE / 'prefix.stdout').open('x') as out, (HERE / 'prefix.stderr').open('x') as err:
    child = subprocess.Popen(command, stdout=out, stderr=err)
    worker = psutil.Process(child.pid)
    parent = psutil.Process()
    while child.poll() is None:
        try:
            peak = max(peak, worker.memory_info().rss + parent.memory_info().rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                child.kill()
                break
        if peak > cfg['combined_rss_cap_bytes']:
            stop = 'RSS_CAP'
        elif time.monotonic() - start >= cfg['parent_wall_cap_seconds']:
            stop = 'PARENT_WALL_CAP'
        if stop:
            child.kill()
            break
        time.sleep(0.02)
    exit_code = child.wait()
output = (HERE / 'prefix.stdout').read_text()
lines = output.splitlines()
native = json.loads(lines[-1]) if exit_code == 0 and len(lines) == 1 else None
status = 'COMPLETE_PREFIX_CENSUS' if native is not None and not stop else (
    'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE')
result = {'status':status,'candidate_id':None,'exit_code':exit_code,
          'stop_reason':stop,'monitor_error':monitor_error,
          'parent_wall_seconds':time.monotonic()-start,
          'sampled_peak_combined_rss_bytes':peak,'rss_samples':samples,
          'native':native,'command':command,'protocol_sha256':sha(cfg_path),
          'stdout_sha256':sha(HERE/'prefix.stdout'),
          'stderr_sha256':sha(HERE/'prefix.stderr')}
(HERE/'prefix_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','parent_wall_seconds','sampled_peak_combined_rss_bytes','native')},sort_keys=True),flush=True)
