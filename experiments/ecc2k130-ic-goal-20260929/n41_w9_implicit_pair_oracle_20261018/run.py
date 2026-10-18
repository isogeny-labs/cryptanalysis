"""Bounded one-worker query of the frozen implicit left-pair oracle panel."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def check_sources(record):
    for name, expected in record['source_sha256'].items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        assert sha(path) == expected, name


def main():
    panel = load('panel_protocol.json')
    cfg = load('query_protocol.json')
    assert panel['status'] == 'FROZEN_BEFORE_PANEL'
    assert cfg['status'] == 'FROZEN_BEFORE_QUERY'
    check_sources(panel)
    check_sources(cfg)
    assert not (HERE / 'query_result.json').exists()
    command = [str(HERE / 'oracle'), 'query', str(HERE / 'join_input.tsv'),
               str(HERE / 'panel.tsv')]
    stdout = HERE / 'query.stdout'
    stderr = HERE / 'query.stderr'
    began = time.monotonic()
    peak = samples = 0
    stop = monitor_error = None
    parent = psutil.Process(os.getpid())
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        worker = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + worker.memory_info().rss)
                samples += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
                if child.poll() is None:
                    monitor_error = type(exc).__name__
                    stop = 'MONITOR_FAILURE'
                    break
            if peak > cfg['rss_cap_bytes']:
                stop = 'RSS_CAP'
                break
            if time.monotonic() - began > cfg['query_wall_cap_seconds']:
                stop = 'WALL_CAP'
                break
            time.sleep(0.01)
        if stop and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        exit_code = child.wait()
    lines = stdout.read_text().splitlines()
    case_lines = [line for line in lines if line.startswith('CASE ')]
    totals = [line for line in lines if line.startswith('TOTAL ')]
    if stop:
        status = 'BOUNDED_UNKNOWN' if stop == 'WALL_CAP' else stop
    elif exit_code == 0 and len(case_lines) == 385 and len(totals) == 1:
        status = 'COMPLETE_PENDING_INDEPENDENT_REPLAY'
    else:
        status = 'PRODUCER_FAILURE'
    result = {'status': status, 'candidate_id': None, 'command': command,
              'exit_code': exit_code, 'stop_reason': stop,
              'monitor_error': monitor_error,
              'parent_wall_seconds': time.monotonic() - began,
              'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
              'case_count': len(case_lines), 'total_lines': totals,
              'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
              'protocol_sha256': sha(HERE / 'query_protocol.json')}
    (HERE / 'query_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
