"""Run the checked builder once with a sampled aggregate RSS limit."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
LAUNCHER = Path('/Volumes/SSD990/cryptanalysis/sage')
protocol = json.loads((HERE / 'protocol.json').read_text())
assert not (HERE / 'build_monitor.json').exists()
assert not (HERE / 'build_result.json').exists()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
with (HERE / 'build.stdout').open('xb') as out, (HERE / 'build.stderr').open('xb') as err:
    child = subprocess.Popen([str(LAUNCHER), '-python', str(HERE / 'build.py')],
                             stdout=out, stderr=err, start_new_session=True)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            children = process.children(recursive=True)
            resident = sum(p.memory_info().rss for p in [process] + children)
            peak = max(peak, resident)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = 'MONITOR_FAILURE'
                break
        if peak > protocol['rss_cap_bytes']:
            stop = 'RSS_CAP'
            break
        if time.monotonic() - started > protocol['build_wall_cap_seconds'] + 10:
            stop = 'WALL_CAP'
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    code = child.wait()
result = {
    'status': 'PASS' if code == 0 and stop is None else 'BUILD_FAILURE',
    'command': [str(LAUNCHER), '-python', str(HERE / 'build.py')],
    'exit_code': code,
    'stop': stop,
    'monitor_error': monitor_error,
    'wall_seconds': time.monotonic() - started,
    'sampled_peak_aggregate_rss_bytes': peak,
    'samples': samples,
    'build_stdout_sha256': sha(HERE / 'build.stdout'),
    'build_stderr_sha256': sha(HERE / 'build.stderr'),
    'monitor_sha256': sha(__file__),
    'protocol_sha256': sha(HERE / 'protocol.json'),
}
(HERE / 'build_monitor.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
