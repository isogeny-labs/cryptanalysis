"""Monitored one-worker launch for the frozen global valid-code norm."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROTO = HERE / 'protocol.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proto = json.loads(PROTO.read_text())
    assert sha(Path(__file__)) == proto['source_sha256']['run.py']
    assert sha(HERE / 'oracle.py') == proto['source_sha256']['oracle.py']
    assert sha(HERE / 'sage_runtime_info.json') == proto['source_sha256']['sage_runtime_info.json']
    assert sha(ROOT / 'n41_w11_freecode_resultant_20261018/resultant_input.tsv') == proto['source_sha256']['resultant_input.tsv']
    assert proto['worker_count'] == 1
    assert proto['command'] == [str(ROOT.parent.parent / 'sage'), '-python', str(HERE / 'oracle.py')]
    start = time.monotonic_ns()
    peak = 0
    stop = None
    monitor_degraded = False
    with (HERE / 'stdout.txt').open('x') as out, (HERE / 'stderr.txt').open('x') as err:
        child = subprocess.Popen(proto['command'], stdout=out, stderr=err, start_new_session=True)
        proc = psutil.Process(child.pid)
        parent = psutil.Process()
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + proc.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                monitor_degraded = child.poll() is None
            if peak > proto['rss_cap_bytes']:
                stop = 'RSS_CAP'
            elif time.monotonic_ns() - start > proto['wall_cap_seconds'] * 10**9:
                stop = 'WALL_CAP'
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    end = time.monotonic_ns()
    result_path = HERE / 'result.json'
    if stop or child.returncode == -signal.SIGALRM:
        status = 'BOUNDED_UNKNOWN'
    elif child.returncode == 0 and result_path.exists() and not (HERE / 'stderr.txt').read_bytes():
        status = 'COMPLETE_GLOBAL_VALID_CODE_NORM'
    else:
        status = 'PRODUCER_FAILURE'
    receipt = {'status': status, 'candidate_id': None, 'exit_code': child.returncode,
               'stop_reason': stop, 'monitor_degraded': monitor_degraded,
               'wall_ns': end - start, 'sampled_peak_combined_rss_bytes': peak,
               'protocol_sha256': sha(PROTO), 'stdout_sha256': sha(HERE / 'stdout.txt'),
               'stderr_sha256': sha(HERE / 'stderr.txt'),
               'result_sha256': sha(result_path) if result_path.exists() else None}
    (HERE / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
