"""Matched fixed-conflict W29 trace-circuit probe for both N131 raw lifts."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRACE = ROOT / 'n41_n131_trace_parity_20261017'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
ORDER = ('raw0', 'raw1', 'raw1', 'raw0')
FORMULAS = {'raw0': TRACE / 'n131_trace.xcnf',
            'raw1': HERE / 'n131_raw1_trace.xcnf'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    build = json.loads((HERE / 'build_n131_raw1_result.json').read_text())
    assert build['status'] == 'PASS_N131_SECOND_LIFT_FORMULAS_BUILT'
    assert sha(FORMULAS['raw1']) == build['formula_sha256']['raw1_trace']
    raw0 = json.loads((TRACE / 'build_n131_result.json').read_text())
    assert sha(FORMULAS['raw0']) == raw0['trace_sha256']
    protocol = {'status': 'FROZEN_N131_TWO_RAW_LIFT_CONFLICT_PROBE',
                'curve_id': build['curve_id'],
                'public_subgroup_point': build['public_subgroup_point'],
                'raw0_point': json.loads((HERE / 'lift_targets.json').read_text())['rows'][1]['raw0'],
                'raw1_point': build['target_raw_point'],
                'order': ORDER, 'conflict_cap': 100000,
                'wall_cap_seconds_per_run': 150,
                'combined_rss_cap_bytes': 4 * 1024**3,
                'worker_count': 1,
                'source_sha256': {name: sha(path) for name, path in
                                  {'script': Path(__file__),
                                   'raw0_formula': FORMULAS['raw0'],
                                   'raw1_formula': FORMULAS['raw1'],
                                   'solver': SOLVER,
                                   'raw1_build': HERE / 'build_n131_raw1_result.json',
                                   'raw0_build': TRACE / 'build_n131_result.json',
                                   'lift_targets': HERE / 'lift_targets.json',
                                   'runtime': HERE / 'sage_runtime_info.json'}.items()}}
    path = HERE / 'probe_n131_lifts_protocol.json'
    with path.open('x') as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write('\n')
    return path, protocol


def main():
    protocol_path, protocol = freeze()
    parent = psutil.Process()
    rows = []
    for index, variant in enumerate(ORDER):
        formula = FORMULAS[variant]
        assert sha(formula) == protocol['source_sha256'][f'{variant}_formula']
        command = [str(SOLVER), '--threads=1', '--maxconfl=100000',
                   '--maxtime=145', '--zero-exit-status', '--verb=1',
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
                if total > protocol['combined_rss_cap_bytes']:
                    stop = 'RSS_CAP'
                    process.kill()
                    break
                if (time.monotonic_ns() - start) / 1e9 >= protocol['wall_cap_seconds_per_run']:
                    stop = 'WALL_CAP'
                    process.kill()
                    break
                time.sleep(0.05)
            exit_code = process.wait()
        elapsed = time.monotonic_ns() - start
        output = stdout_path.read_text(errors='replace')
        status_lines = [line for line in output.splitlines() if line.startswith('s ')]
        def metric(label):
            matches = [m.group(1) for line in output.splitlines()
                       if (m := re.match(r'c ' + label + r'\s*:\s*(\d+[KMG]?)\b', line))]
            return matches[-1] if matches else None
        row = {'index': index, 'variant': variant, 'status_lines': status_lines,
               'conflicts': metric('conflicts'), 'decisions': metric('decisions'),
               'propagations': metric('propagations'),
               'elapsed_ns': elapsed, 'sampled_peak_combined_rss_bytes': peak,
               'stop_reason': stop, 'exit_code': exit_code,
               'command': command, 'formula_sha256': sha(formula),
               'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
        rows.append(row)
        print(json.dumps({'index': index, 'variant': variant,
                          'elapsed_seconds': elapsed / 1e9,
                          'status_lines': status_lines,
                          'conflicts': row['conflicts'],
                          'decisions': row['decisions'],
                          'propagations': row['propagations'],
                          'stop_reason': stop}), flush=True)
    result = {'status': 'COMPLETE_N131_TWO_RAW_LIFT_CONFLICT_PROBE',
              'rows': rows, 'protocol_sha256': sha(protocol_path)}
    with (HERE / 'probe_n131_lifts_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')


if __name__ == '__main__':
    main()
