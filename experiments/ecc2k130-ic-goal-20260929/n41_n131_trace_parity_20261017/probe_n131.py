"""Matched 100k-conflict N131 public-point probe for the global trace row."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
ORDER = ('baseline', 'trace', 'trace', 'baseline')
FORMULAS = {'baseline': HERE / 'n131_baseline.xcnf',
            'trace': HERE / 'n131_trace.xcnf'}
CONFLICT_CAP = 100000
WALL_CAP = 120
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = {'status': 'FROZEN_N131_TRACE_PARITY_CONFLICT_PROBE',
            'curve_id': json.loads((HERE / 'build_n131_result.json').read_text())['curve_id'],
            'order': ORDER, 'conflict_cap': CONFLICT_CAP,
            'wall_cap_seconds_per_run': WALL_CAP,
            'combined_rss_cap_bytes': RSS_CAP, 'worker_count': 1,
            'source_sha256': {name: sha(path) for name, path in
                              {'script': Path(__file__), 'baseline': FORMULAS['baseline'],
                               'trace': FORMULAS['trace'], 'solver': SOLVER,
                               'build': HERE / 'build_n131_result.json',
                               'census': HERE / 'census_trace_result.json',
                               'runtime': HERE / 'sage_runtime_info.json'}.items()}}
protocol_path = HERE / 'probe_n131_protocol.json'
with protocol_path.open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')
rows = []
parent = psutil.Process()
for index, variant in enumerate(ORDER):
    formula = FORMULAS[variant]
    assert sha(formula) == protocol['source_sha256'][variant]
    command = [str(SOLVER), '--threads=1', f'--maxconfl={CONFLICT_CAP}',
               '--maxtime=115', '--zero-exit-status', '--verb=1',
               '--printsol=1', str(formula)]
    stdout_path = HERE / f'probe_n131_{index}_{variant}.stdout'
    stderr_path = HERE / f'probe_n131_{index}_{variant}.stderr'
    start = time.monotonic_ns()
    stop = None
    peak = parent.memory_info().rss
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        worker = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                total = parent.memory_info().rss + worker.memory_info().rss
                peak = max(peak, total)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if process.poll() is None:
                    stop = 'MONITOR_FAILURE'
                    process.kill()
                break
            if total > RSS_CAP:
                stop = 'RSS_CAP'
                process.kill()
                break
            if (time.monotonic_ns() - start) / 1e9 >= WALL_CAP:
                stop = 'WALL_CAP'
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    elapsed = time.monotonic_ns() - start
    output = stdout_path.read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    conflicts = [int(match.group(1)) for line in output.splitlines()
                 if (match := re.match(r'c conflicts\s*:\s*(\d+)', line))]
    row = {'index': index, 'variant': variant, 'status_lines': statuses,
           'conflicts': conflicts, 'elapsed_ns': elapsed,
           'sampled_peak_combined_rss_bytes': peak,
           'stop_reason': stop, 'exit_code': exit_code,
           'command': command, 'formula_sha256': sha(formula),
           'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
    rows.append(row)
    print(json.dumps({'index': index, 'variant': variant,
                      'elapsed_seconds': elapsed / 1e9,
                      'status_lines': statuses, 'conflicts': conflicts,
                      'stop_reason': stop}), flush=True)
result = {'status': 'COMPLETE_N131_TRACE_PARITY_CONFLICT_PROBE',
          'rows': rows, 'protocol_sha256': sha(protocol_path)}
with (HERE / 'probe_n131_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
