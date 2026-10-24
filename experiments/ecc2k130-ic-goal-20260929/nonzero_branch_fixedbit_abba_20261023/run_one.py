"""Run one frozen old/new cubic branch arm with process-tree resource receipts."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / 'protocol.json').read_text())
assert cfg['status'] == 'FROZEN_BEFORE_FIXEDBIT_ABBA_RUNS'
for path, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path

panel = sys.argv[1]
index = int(sys.argv[2])
assert panel in ('positive', 'ordinary')
assert 0 <= index < len(cfg['arm_order'])
arm = cfg['arm_order'][index]
source = Path(cfg['arms'][arm]['directory'])
case = cfg['arms'][arm]['cases'][panel]
run_dir = HERE / f'{panel}_{index}_{arm}'
assert not run_dir.exists(), run_dir
run_dir.mkdir()
shutil.copy2(source / 'branch_gb.py', run_dir / 'branch_gb.py')
shutil.copy2(source / 'protocol.json', run_dir / 'protocol.json')
assert hashlib.sha256((run_dir / 'branch_gb.py').read_bytes()).hexdigest() == cfg['sources'][str(source / 'branch_gb.py')]
assert hashlib.sha256((run_dir / 'protocol.json').read_bytes()).hexdigest() == cfg['sources'][str(source / 'protocol.json')]

command = [cfg['sage_launcher'], '-python', str(run_dir / 'branch_gb.py'), case]
stdout = run_dir / 'stdout.log'
stderr = run_dir / 'stderr.log'
started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
with stdout.open('xb') as out, stderr.open('xb') as err:
    child = subprocess.Popen(command, cwd=run_dir, stdout=out, stderr=err,
                             start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, observed.memory_info().rss + psutil.Process(os.getpid()).memory_info().rss)
            samples += 1
        except psutil.NoSuchProcess:
            if child.poll() is not None:
                break
            time.sleep(0.1)
            if child.poll() is not None:
                break
            monitor_error = 'NoSuchProcessWhileLive'
            stop = 'MONITOR_FAILURE'
            break
        except (psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > cfg['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic() - started > cfg['wall_cap_seconds']:
            stop = 'WALL_CAP'
            break
        time.sleep(0.1)
    if stop and child.poll() is None:
        try:
            child.terminate()
        except ProcessLookupError:
            pass
    exit_code = child.wait()

result_path = run_dir / (case + '_result.json')
status = 'COMPLETE' if not stop and exit_code == 0 and result_path.exists() else (stop or 'PRODUCER_FAILURE')
receipt = {
    'status': status, 'candidate_id': None, 'panel': panel, 'index': index,
    'arm': arm, 'case': case, 'command': command, 'exit_code': exit_code,
    'wall_seconds': time.monotonic() - started, 'sampled_peak_combined_rss_bytes': peak,
    'rss_samples': samples, 'stop_reason': stop, 'monitor_error': monitor_error,
    'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest(),
    'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest() if result_path.exists() else None,
    'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest(),
    'arm_protocol_sha256': hashlib.sha256((run_dir / 'protocol.json').read_bytes()).hexdigest(),
    'arm_source_sha256': hashlib.sha256((run_dir / 'branch_gb.py').read_bytes()).hexdigest(),
}
with (run_dir / 'receipt.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps({k: receipt[k] for k in ('panel', 'index', 'arm', 'status', 'wall_seconds', 'sampled_peak_combined_rss_bytes')}, sort_keys=True))
