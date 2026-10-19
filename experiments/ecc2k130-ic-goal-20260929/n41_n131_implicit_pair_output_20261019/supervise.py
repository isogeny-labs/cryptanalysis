"""Run one bounded native implicit-membership worker and retain its receipt."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in ('n41', 'n131')
    label = sys.argv[1]
    protocol = HERE / f'query_protocol_{label}.json'
    cfg = json.loads(protocol.read_text())
    assert cfg['status'] == f'FROZEN_BEFORE_IMPLICIT_PAIR_{label.upper()}'
    assert cfg['worker_count'] == 1 and cfg['wall_cap_seconds'] == 120
    assert cfg['rss_cap_bytes'] == 4294967296
    assert cfg['supervisor_sha256'] == sha(__file__)
    for rec in [cfg['binary'], cfg['input'], *cfg['dependencies'].values()]:
        assert sha(rec['path']) == rec['sha256']
    command = [cfg['binary']['path'], cfg['input']['path']]
    out = HERE / f'{label}.stdout'
    err = HERE / f'{label}.stderr'
    start = time.monotonic()
    peak = samples = 0
    stop = None
    parent = psutil.Process(os.getpid())
    with out.open('xb') as stdout, err.open('xb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                 cwd=HERE, start_new_session=True)
        (HERE / f'{label}.handle.json').write_text(json.dumps({
            'pid': child.pid, 'command': command, 'started_monotonic': start},
            sort_keys=True, indent=2) + '\n')
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
                samples += 1
            except psutil.NoSuchProcess:
                if child.poll() is not None:
                    break
                continue
            if peak > cfg['rss_cap_bytes']:
                stop = 'RSS_CAP'
                break
            if time.monotonic() - start > cfg['wall_cap_seconds']:
                stop = 'WALL_CAP'
                break
            time.sleep(0.02)
        if stop and child.poll() is None:
            child.terminate()
        code = child.wait()
    lines = out.read_text(errors='replace').splitlines()
    finals = [line for line in lines if line.startswith('RESULT ')]
    if stop:
        status = stop
    elif code != 0:
        status = 'PRODUCER_FAILURE'
    elif len(finals) == 1 and finals[0].split()[1] == 'COMPLETE':
        status = 'COMPLETE'
    elif len(finals) == 1 and finals[0].split()[1] == 'WALL_CAP':
        status = 'WORKER_WALL_CAP'
    else:
        status = 'SCHEMA_INCOMPLETE'
    receipt = {'status': status, 'candidate_id': None, 'label': label,
               'command': command, 'exit_code': code, 'stop_reason': stop,
               'wall_seconds': time.monotonic() - start,
               'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
               'stdout_sha256': sha(out), 'stderr_sha256': sha(err),
               'binary_sha256': sha(cfg['binary']['path']),
               'input_sha256': sha(cfg['input']['path']),
               'protocol_sha256': sha(protocol), 'supervisor_sha256': sha(__file__)}
    (HERE / f'{label}.receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
