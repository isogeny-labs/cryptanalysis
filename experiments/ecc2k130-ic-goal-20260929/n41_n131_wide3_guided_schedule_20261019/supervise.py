"""Run each frozen sparse block query with one bounded native worker."""
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


def one_query(cfg, label):
    rec = cfg['inputs'][label]
    command = [cfg['binary']['path'], rec['path'], cfg['schedule']['path']]
    stdout = HERE / (label + '.stdout')
    stderr = HERE / (label + '.stderr')
    receipt = HERE / (label + '.receipt.json')
    assert not stdout.exists() and not stderr.exists() and not receipt.exists()
    start = time.monotonic()
    parent = psutil.Process(os.getpid())
    peak = samples = 0
    stop = None
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, cwd=HERE,
                                 start_new_session=True)
        (HERE / (label + '.handle.json')).write_text(json.dumps({
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
            time.sleep(0.02)
        if stop and child.poll() is None:
            child.terminate()
        code = child.wait()
    lines = stdout.read_text(errors='replace').splitlines()
    rejects = [line for line in lines if line.startswith('REJECT_CERTIFICATE ')]
    unresolved = [line for line in lines if line.startswith('UNRESOLVED_AT_DEGREE6 ')]
    if stop:
        status = stop
    elif code != 0:
        status = 'PRODUCER_FAILURE'
    elif len(rejects) == 1 and not unresolved and any(line.startswith('CERT_ROWS') for line in lines):
        status = 'REJECT_CERTIFICATE'
    elif len(unresolved) == 1 and not rejects:
        status = 'UNRESOLVED_AT_DEGREE6'
    else:
        status = 'SCHEMA_INCOMPLETE'
    result = {'label': label, 'status': status, 'candidate_id': None,
              'command': command, 'exit_code': code, 'stop_reason': stop,
              'wall_seconds': time.monotonic() - start, 'rss_samples': samples,
              'sampled_peak_combined_rss_bytes': peak,
              'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
              'input_sha256': sha(rec['path']), 'binary_sha256': sha(cfg['binary']['path']),
              'schedule_sha256': sha(cfg['schedule']['path']),
              'protocol_sha256': sha(HERE / cfg['protocol_name']),
              'supervisor_sha256': sha(__file__)}
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
          ['label', 'status', 'wall_seconds', 'sampled_peak_combined_rss_bytes']},
          sort_keys=True), flush=True)
    return result


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in ('n41', 'n131')
    protocol_name = 'query_protocol_' + sys.argv[1] + '.json'
    cfg = json.loads((HERE / protocol_name).read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_BLOCK_' + sys.argv[1].upper()
    assert cfg['protocol_name'] == protocol_name and cfg['worker_count'] == 1
    assert sha(__file__) == cfg['supervisor_sha256']
    assert sha(cfg['binary']['path']) == cfg['binary']['sha256']
    assert sha(cfg['schedule']['path']) == cfg['schedule']['sha256']
    for rec in cfg['dependencies'].values():
        assert sha(rec['path']) == rec['sha256']
    for rec in cfg['inputs'].values():
        assert sha(rec['path']) == rec['sha256']
    results = []
    for label in cfg['labels']:
        row = one_query(cfg, label)
        results.append(row)
        if cfg['stop_after_nonterminal'] and (
                row['status'] not in ('REJECT_CERTIFICATE', 'UNRESOLVED_AT_DEGREE6') or
                (len(results) == 1 and row['status'] != cfg['expected_first_status'])):
            break
    summary = {'status': 'COMPLETE_PANEL' if len(results) == len(cfg['labels']) else
               'PARTIAL_PANEL', 'candidate_id': None, 'curve_id': cfg['curve_id'],
               'labels_requested': cfg['labels'], 'labels_executed': [r['label'] for r in results],
               'statuses': [r['status'] for r in results],
               'protocol_sha256': sha(HERE / protocol_name),
               'supervisor_sha256': sha(__file__)}
    (HERE / ('query_result_' + sys.argv[1] + '.json')).write_text(
        json.dumps(summary, sort_keys=True, indent=2) + '\n')
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
