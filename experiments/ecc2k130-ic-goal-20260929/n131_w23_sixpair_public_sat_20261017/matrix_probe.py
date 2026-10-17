"""Matched conflict-limit screen of local XOR-matrix admission on W23."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

BASE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
FORMULA = BASE / 'ordinary.xcnf'
RSS_CAP = 4294967296


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (BASE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def freeze():
    main_result = json.loads((BASE / 'result.json').read_text())
    assert main_result['status'] == 'BOUNDED_UNKNOWN'
    assert main_result['formula_sha256'] == sha(FORMULA)
    save('matrix_protocol.json', {
        'status': 'FROZEN_W23_MATRIX_POLICY_CONFLICT_SCREEN',
        'candidate_id': None, 'curve_id': main_result['curve_id'],
        'workload_id': main_result['workload_id'],
        'worker_count': 1, 'arms': ['default', 'wide'],
        'conflict_cap': 100000, 'solver_seconds_cap': 100,
        'parent_seconds_cap_per_arm': 110, 'combined_rss_cap_bytes': RSS_CAP,
        'shared_flags': ['--threads=1', '--maxconfl=100000', '--maxtime=100',
                         '--zero-exit-status', '--verb=1'],
        'wide_flags': ['--maxmatrixrows=4096', '--maxmatrixcols=10000',
                       '--maxnummatrices=12'],
        'source_sha256': {'script': sha(Path(__file__)),
                          'formula': sha(FORMULA), 'solver': sha(SOLVER),
                          'public_query': sha(BASE / 'result.json')}})


def run():
    protocol = json.loads((BASE / 'matrix_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_W23_MATRIX_POLICY_CONFLICT_SCREEN'
    assert protocol['source_sha256'] == {
        'script': sha(Path(__file__)), 'formula': sha(FORMULA),
        'solver': sha(SOLVER), 'public_query': sha(BASE / 'result.json')}
    parent = psutil.Process()
    arms = []
    for name in protocol['arms']:
        flags = protocol['shared_flags'] + (protocol['wide_flags'] if name == 'wide' else [])
        command = [str(SOLVER), *flags, str(FORMULA)]
        start = time.monotonic_ns()
        peak = parent.memory_info().rss
        stop = None
        with (BASE / f'matrix_{name}.stdout').open('x') as stdout, \
             (BASE / f'matrix_{name}.stderr').open('x') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    combined = parent.memory_info().rss + child.memory_info().rss
                    peak = max(peak, combined)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    stop = 'MONITOR_FAILURE'
                    process.kill()
                    break
                if combined > RSS_CAP:
                    stop = 'RSS_CAP'
                    process.kill()
                    break
                if time.monotonic_ns() - start >= 110_000_000_000:
                    stop = 'PARENT_CAP'
                    process.kill()
                    break
                time.sleep(0.05)
            code = process.wait()
        elapsed = time.monotonic_ns() - start
        outpath = BASE / f'matrix_{name}.stdout'
        errpath = BASE / f'matrix_{name}.stderr'
        output = outpath.read_text(errors='replace')
        matrix_lines = [line for line in output.splitlines()
                        if '[matrix]' in line or 'Using ' in line and 'matrices' in line]
        restarts = [line for line in output.splitlines() if line.startswith('c rst')]
        statuses = [line for line in output.splitlines() if line.startswith('s ')]
        row = {'name': name, 'command': command, 'exit_code': code,
               'stop_reason': stop, 'status_lines': statuses,
               'elapsed_ns': elapsed, 'sampled_peak_combined_rss_bytes': peak,
               'restart_count': len(restarts),
               'first_restart': restarts[0] if restarts else None,
               'last_restart': restarts[-1] if restarts else None,
               'matrix_lines': matrix_lines,
               'stdout_sha256': sha(outpath), 'stderr_sha256': sha(errpath)}
        arms.append(row)
        print(json.dumps({'arm': name, 'exit_code': code,
                          'stop_reason': stop, 'restarts': len(restarts),
                          'elapsed_seconds': elapsed / 1e9}), flush=True)
    save('matrix_result.json', {'status': 'COMPLETE_MATRIX_POLICY_SCREEN',
        'candidate_id': None, 'arms': arms,
        'protocol_sha256': sha(BASE / 'matrix_protocol.json'),
        'source_sha256': protocol['source_sha256']})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
