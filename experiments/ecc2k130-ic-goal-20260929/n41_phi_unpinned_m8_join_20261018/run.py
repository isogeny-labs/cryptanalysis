"""Monitor one frozen N41 phi 4+4 join arm."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(label):
    assert label in ('positive', 'public')
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_N41_PHI_UNPINNED_M8_JOIN'
    assert cfg['candidate_id'] is None and cfg['worker_count'] == 1
    assert cfg['wall_cap_seconds'] == 600 and cfg['rss_cap_bytes'] == 4 * 1024**3
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    command = [str(HERE / 'join'), str(HERE / f'{label}_input.tsv'),
               '590', str(cfg['rss_cap_bytes'])]
    assert command == cfg['commands'][label]
    stdout = HERE / f'{label}.stdout'
    stderr = HERE / f'{label}.stderr'
    receipt_path = HERE / f'{label}_receipt.json'
    assert not stdout.exists() and not stderr.exists() and not receipt_path.exists()
    start = time.monotonic_ns()
    stop = None
    peak = samples = misses = 0
    parent = psutil.Process(os.getpid())
    with stdout.open('x') as out, stderr.open('x') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err,
                                 start_new_session=True)
        worker = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + worker.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    misses += 1
            if peak > cfg['rss_cap_bytes']:
                stop = 'RSS_CAP'
            elif time.monotonic_ns() - start >= cfg['wall_cap_seconds'] * 10**9:
                stop = 'WALL_CAP'
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    lines = stdout.read_text().splitlines()
    hits = [line for line in lines if line.startswith('HIT ')]
    if stop or child.returncode in (2, 3):
        status = 'BOUNDED_UNKNOWN' if stop != 'RSS_CAP' and child.returncode != 3 else 'RESOURCE_CAP'
    elif child.returncode == 0 and misses == 0 and not stderr.read_bytes() and len(hits) == 1:
        status = 'COMPLETE_HIT'
    elif child.returncode == 0 and misses == 0 and not stderr.read_bytes() and lines[-1].startswith('MISS_COMPLETE '):
        status = 'COMPLETE_MISS'
    else:
        status = 'PRODUCER_FAILURE'
    receipt = {'status': status, 'candidate_id': None, 'arm': label,
               'exit_code': child.returncode, 'stop_reason': stop,
               'monitor_misses': misses, 'rss_samples': samples,
               'sampled_peak_combined_rss_bytes': peak,
               'wall_ns': time.monotonic_ns() - start,
               'hit_lines': hits, 'protocol_sha256': sha(cfg_path),
               'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)}
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if status in ('COMPLETE_HIT', 'COMPLETE_MISS') else 1


if __name__ == '__main__':
    assert len(sys.argv) == 2
    raise SystemExit(main(sys.argv[1]))
