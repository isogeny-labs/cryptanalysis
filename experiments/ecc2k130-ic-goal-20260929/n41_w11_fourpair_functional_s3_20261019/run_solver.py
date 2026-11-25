"""Run the frozen one-thread functional-S3 public query under parent caps."""
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
    cfg = json.loads((HERE / 'query_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_FUNCTIONAL_S3_QUERY'
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    assert cfg['worker_count'] == 1
    out, err = HERE / 'solver.stdout', HERE / 'solver.stderr'
    result_path = HERE / 'query_result.json'
    assert not out.exists() and not err.exists() and not result_path.exists()
    command = [cfg['solver'], *cfg['solver_flags'], cfg['sources']['formula']['path']]
    start = time.monotonic()
    parent = psutil.Process(os.getpid())
    peak = samples = 0
    stop = None
    with out.open('xb') as stdout, err.open('xb') as stderr:
        child = subprocess.Popen(command, cwd=HERE, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        (HERE / 'query_handle.json').write_text(json.dumps({
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
                stop = 'MONITOR_FAILURE'
                break
            except (psutil.AccessDenied, PermissionError):
                if child.poll() is None:
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
    lines = out.read_text(errors='replace').splitlines()
    sat = any(line.strip() == 's SATISFIABLE' for line in lines)
    unsat = any(line.strip() == 's UNSATISFIABLE' for line in lines)
    assert not (sat and unsat)
    status = ('SAT_MODEL_PENDING_AUDIT' if sat and not stop else
              'UNSAT_SOLVER_STATUS' if unsat and not stop else stop or 'BOUNDED_UNKNOWN')
    result = {'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
              'command': command, 'exit_code': code,
              'wall_seconds': time.monotonic() - start,
              'sampled_peak_combined_rss_bytes': peak, 'rss_samples': samples,
              'stop_reason': stop, 'terminal_sat_line': sat,
              'terminal_unsat_line': unsat, 'stdout_sha256': sha(out),
              'stderr_sha256': sha(err), 'protocol_sha256': sha(HERE / 'query_protocol.json'),
              'runner_sha256': sha(__file__)}
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
          ('status', 'exit_code', 'wall_seconds', 'sampled_peak_combined_rss_bytes')},
          sort_keys=True))


if __name__ == '__main__':
    main()
