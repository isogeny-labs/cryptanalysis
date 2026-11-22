"""Matched fixed-conflict diagnostic for original, aligned, ordered W9."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
ORDER = ('original', 'aligned', 'ordered', 'ordered', 'aligned', 'original')
FORMULAS = {'original': HERE / 'n41_original.xcnf',
            'aligned': HERE / 'n41_aligned.xcnf',
            'ordered': HERE / 'n41_aligned_ordered.xcnf'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = json.loads((HERE / 'build_n41_result.json').read_text())
    ordered = json.loads((HERE / 'build_n41_ordered_result.json').read_text())
    assert base['status'] == 'PASS_N41_ALIGNED_MODEL_AND_MATCHED_FORMULAS'
    assert ordered['status'] == 'PASS_N41_ALIGNED_ORDERED_MODEL'
    assert all(sha(FORMULAS[name]) == base['rows'][name]['formula_sha256']
               for name in ('original', 'aligned'))
    assert sha(FORMULAS['ordered']) == ordered['formula_sha256']
    protocol = {'status': 'FROZEN_N41_ALIGNED_CONFLICT_PROBE',
                'curve_id': base['curve_id'],
                'raw_oriented_point': base['raw_oriented_point'],
                'order': ORDER, 'conflict_cap': 50000,
                'wall_cap_seconds_per_run': 90,
                'combined_rss_cap_bytes': 4 * 1024**3,
                'worker_count': 1,
                'source_sha256': {name: sha(path) for name, path in
                                  {'script': Path(__file__), 'solver': SOLVER,
                                   'original_formula': FORMULAS['original'],
                                   'aligned_formula': FORMULAS['aligned'],
                                   'ordered_formula': FORMULAS['ordered'],
                                   'base_build': HERE / 'build_n41_result.json',
                                   'ordered_build': HERE / 'build_n41_ordered_result.json',
                                   'model_fixture': HERE / 'n41_model_fixture.json',
                                   'runtime': HERE / 'sage_runtime_info.json'}.items()}}
    protocol_path = HERE / 'probe_n41_protocol.json'
    with protocol_path.open('x') as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write('\n')
    parent = psutil.Process()
    rows = []
    for index, variant in enumerate(ORDER):
        formula = FORMULAS[variant]
        assert sha(formula) == protocol['source_sha256'][f'{variant}_formula']
        command = [str(SOLVER), '--threads=1', '--maxconfl=50000',
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
            values = [m.group(1) for line in output.splitlines()
                      if (m := re.match(r'c ' + label + r'\s*:\s*(\d+[KMG]?)\b', line))]
            return values[-1] if values else None
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
    result = {'status': 'COMPLETE_N41_ALIGNED_CONFLICT_PROBE',
              'rows': rows, 'protocol_sha256': sha(protocol_path)}
    with (HERE / 'probe_n41_result.json').open('x') as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write('\n')


if __name__ == '__main__':
    main()
