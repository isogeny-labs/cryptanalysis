"""Matched N41 public-point inverse-output versus exact-source SAT probe."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
FORMULAS = {'exact_source': HERE / 'n41_exact5_output_trace.xcnf',
            'inverse_output': HERE / 'n41_inverse_output_trace.xcnf'}
ORDER = ('exact_source', 'inverse_output', 'inverse_output', 'exact_source')
CONFLICT_CAP = 100000
WALL_CAP = 90
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = {'status': 'FROZEN_N41_INVERSE_OUTPUT_CONFLICT_PROBE',
            'curve_id': json.loads((HERE / 'build_n41_result.json').read_text())['curve_id'],
            'order': ORDER, 'conflict_cap': CONFLICT_CAP,
            'wall_cap_seconds_per_run': WALL_CAP,
            'combined_rss_cap_bytes': RSS_CAP,
            'worker_count': 1,
            'source_sha256': {key: sha(path) for key, path in
                              {'script': Path(__file__), 'solver': SOLVER,
                               'exact_source': FORMULAS['exact_source'],
                               'inverse_output': FORMULAS['inverse_output'],
                               'inverse_build': HERE / 'build_n41_result.json',
                               'baseline_build': HERE / 'baseline_n41_result.json',
                               'runtime': HERE / 'sage_runtime_info.json'}.items()}}
protocol_path = HERE / 'probe_n41_protocol.json'
with protocol_path.open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')

rows = []
parent = psutil.Process()
for index, variant in enumerate(ORDER):
    formula = FORMULAS[variant]
    assert sha(formula) == protocol['source_sha256'][variant]
    command = [str(SOLVER), '--threads=1', f'--maxconfl={CONFLICT_CAP}',
               '--maxtime=85', '--zero-exit-status', '--verb=1',
               '--printsol=1', str(formula)]
    stdout_path = HERE / f'probe_n41_{index}_{variant}.stdout'
    stderr_path = HERE / f'probe_n41_{index}_{variant}.stderr'
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
            if (time.monotonic_ns() - start)/1e9 >= WALL_CAP:
                stop = 'WALL_CAP'
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    elapsed = time.monotonic_ns() - start
    output = stdout_path.read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    def stat(name):
        hits = re.findall(r'^c ' + re.escape(name) + r'\s*:\s*([^\n]+)',
                          output, re.M)
        return hits[-1].strip() if hits else None
    row = {'index': index, 'variant': variant, 'status_lines': statuses,
           'conflicts': stat('conflicts'), 'decisions': stat('decisions'),
           'propagations': stat('propagations'),
           'solver_thread_time': stat('Total time (this thread)'),
           'elapsed_ns': elapsed, 'stop_reason': stop, 'exit_code': exit_code,
           'sampled_peak_combined_rss_bytes': peak,
           'command': command, 'formula_sha256': sha(formula),
           'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
    rows.append(row)
    print(json.dumps({'index': index, 'variant': variant,
                      'status_lines': statuses, 'conflicts': row['conflicts'],
                      'elapsed_seconds': elapsed/1e9, 'stop_reason': stop}), flush=True)
result = {'status': 'COMPLETE_N41_INVERSE_OUTPUT_CONFLICT_PROBE',
          'rows': rows, 'protocol_sha256': sha(protocol_path)}
with (HERE / 'probe_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
