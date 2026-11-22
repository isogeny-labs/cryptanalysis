"""Replay the frozen full W20 code-linear scan on the W33 public residual."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol_path = HERE / 'protocol.json'
    cfg = json.loads(protocol_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_W33_PUBLIC_REPLAY'
    assert cfg['candidate_id'] is None and cfg['worker_count'] == 1
    assert cfg['wall_cap_seconds'] == 600 and cfg['rss_cap_bytes'] == 4 * 1024**3
    for name, entry in cfg['sources'].items():
        assert sha(entry['path']) == entry['sha256'], name
    assert cfg['command'] == [cfg['binary'], str(HERE / 'fixture.txt'), cfg['support'],
                              cfg['valid_bitmap'], str(HERE / 'native_result.json'),
                              '590', str(cfg['rss_cap_bytes'])]
    for label in ('receipt.json', 'native_result.json', 'native.stdout', 'native.stderr'):
        assert not (HERE / label).exists(), label
    start = time.monotonic_ns()
    peak = 0
    samples = 0
    stop = None
    monitor_failures = 0
    parent = psutil.Process(os.getpid())
    with (HERE / 'native.stdout').open('x') as out, (HERE / 'native.stderr').open('x') as err:
        child = subprocess.Popen(cfg['command'], stdout=out, stderr=err,
                                 start_new_session=True)
        worker = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + worker.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    monitor_failures += 1
            if peak > cfg['rss_cap_bytes']:
                stop = 'RSS_CAP'
            elif time.monotonic_ns() - start >= cfg['wall_cap_seconds'] * 10**9:
                stop = 'WALL_CAP'
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    native_path = HERE / 'native_result.json'
    try:
        native = json.loads(native_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        native = None
    if stop or native and native['status'] == 'CENSORED_TIME':
        status = 'BOUNDED_UNKNOWN'
    elif (child.returncode == 0 and monitor_failures == 0 and
          not (HERE / 'native.stderr').read_bytes() and native and
          native['status'] == 'COMPLETE_CODE_LINEAR'):
        status = 'COMPLETE_CODE_LINEAR_W33_PUBLIC_REPLAY'
    else:
        status = 'PRODUCER_FAILURE'
    receipt = {
        'status': status, 'candidate_id': None, 'exit_code': child.returncode,
        'stop_reason': stop, 'monitor_failures': monitor_failures,
        'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
        'wall_ns': time.monotonic_ns() - start,
        'protocol_sha256': sha(protocol_path),
        'stdout_sha256': sha(HERE / 'native.stdout'),
        'stderr_sha256': sha(HERE / 'native.stderr'),
        'native_result_sha256': sha(native_path) if native_path.exists() else None,
    }
    (HERE / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if status == 'COMPLETE_CODE_LINEAR_W33_PUBLIC_REPLAY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
