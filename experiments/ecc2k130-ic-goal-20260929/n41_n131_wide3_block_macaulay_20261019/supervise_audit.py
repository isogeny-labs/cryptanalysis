"""Bound the independent Sage block-certificate audit."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_WIDE3_INPUT_SAGE_AUDIT'
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    assert sha(__file__) == cfg['supervisor_sha256']
    command = ['/Volumes/SSD990/cryptanalysis/sage', '-python', cfg['sources']['auditor']['path']]
    stdout, stderr = HERE / 'audit.stdout', HERE / 'audit.stderr'
    receipt = HERE / 'audit_receipt.json'
    assert not stdout.exists() and not stderr.exists() and not receipt.exists()
    start = time.monotonic()
    parent = psutil.Process(os.getpid())
    peak = samples = 0
    stop = None
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, cwd=HERE,
                                 start_new_session=True)
        (HERE / 'audit_handle.json').write_text(json.dumps({'pid': child.pid,
            'started_monotonic': start, 'command': command}, sort_keys=True, indent=2) + '\n')
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
                samples += 1
            except psutil.NoSuchProcess:
                if child.poll() is not None:
                    break
                try:
                    child.wait(timeout=0.25)
                    break
                except subprocess.TimeoutExpired:
                    stop = 'MONITOR_FAILURE'
                    break
            if peak > cfg['rss_cap_bytes']:
                stop = 'RSS_CAP'
                break
            if time.monotonic() - start > cfg['wall_cap_seconds']:
                stop = 'WALL_CAP'
                break
            time.sleep(.02)
        if stop and child.poll() is None:
            child.terminate()
        code = child.wait()
    result = {'status': stop or ('COMPLETE' if code == 0 else 'PRODUCER_FAILURE'),
              'exit_code': code, 'wall_seconds': time.monotonic() - start,
              'stop_reason': stop, 'sampled_peak_combined_rss_bytes': peak,
              'rss_samples': samples, 'stdout_sha256': sha(stdout),
              'stderr_sha256': sha(stderr),
              'result_sha256': sha(HERE / 'audit_result.json') if
                  (HERE / 'audit_result.json').exists() else None,
              'protocol_sha256': sha(HERE / 'audit_protocol.json'),
              'supervisor_sha256': sha(__file__)}
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
          ['status', 'exit_code', 'wall_seconds', 'sampled_peak_combined_rss_bytes']},
          sort_keys=True))


if __name__ == '__main__':
    main()
