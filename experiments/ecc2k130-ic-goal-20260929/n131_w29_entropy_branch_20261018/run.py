"""Capped first-mask-prefix branch of frozen N131 W29 public XCNF."""
import gzip
import hashlib
import json
import resource
import subprocess
import tempfile
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def compress(source, destination):
    with Path(source).open('rb') as inp, gzip.open(destination, 'xb', compresslevel=9) as out:
        for block in iter(lambda: inp.read(1 << 20), b''):
            out.write(block)


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_BRANCH'
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    assert cfg['mask_bit_positions'] == list(range(8))
    assert cfg['mask_variable_ids'] == list(range(1, 9))
    assert cfg['branch_prefix_value'] == 3
    original = Path(cfg['sources']['original_xcnf']['path'])
    parent = psutil.Process()
    started = time.monotonic_ns()
    phase = {}
    with tempfile.TemporaryDirectory(prefix='n131_w29_entropy_branch_', dir='/private/tmp') as temp:
        temp = Path(temp)
        formula = temp / 'branch.xcnf'
        with original.open('r') as source, formula.open('w') as output:
            header = source.readline().strip().split()
            assert header == ['p', 'cnf', '121204', '274931']
            output.write('p cnf 121204 274939\n')
            for i, variable in enumerate(cfg['mask_variable_ids']):
                lit = variable if (cfg['branch_prefix_value'] >> i) & 1 else -variable
                output.write(f'{lit} 0\n')
            for line in source:
                output.write(line)
        phase['formula_patch_ns'] = time.monotonic_ns() - started
        formula_hash = sha(formula)
        phase['formula_hash_ns'] = time.monotonic_ns() - started - phase['formula_patch_ns']
        stdout_path = temp / 'solver.stdout'
        stderr_path = temp / 'solver.stderr'
        command = [cfg['sources']['solver']['path'], *cfg['solver_flags'], str(formula)]
        peak = 0
        samples = 0
        stop = None
        monitor_error = None
        search_start = time.monotonic_ns()
        with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    peak = max(peak, parent.memory_info().rss + child.memory_info().rss)
                    samples += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
                    if process.poll() is None:
                        monitor_error = type(exc).__name__
                        stop = 'MONITOR_FAILURE'
                        process.kill()
                        break
                if peak > cfg['combined_rss_cap_bytes']:
                    stop = 'RSS_CAP'
                elif (time.monotonic_ns() - started) / 1e9 >= cfg['parent_wall_cap_seconds']:
                    stop = 'PARENT_WALL_CAP'
                if stop:
                    process.kill()
                    break
                time.sleep(0.05)
            exit_code = process.wait()
        phase['solver_and_monitor_ns'] = time.monotonic_ns() - search_start
        raw_stdout_hash, raw_stderr_hash = sha(stdout_path), sha(stderr_path)
        output = stdout_path.read_text(errors='replace')
        lines = output.splitlines()
        statuses = [line for line in lines if line.startswith('s ')]
        model_lines = [line for line in lines if line.startswith('v ')]
        if stop in ('MONITOR_FAILURE', 'RSS_CAP'):
            status = stop
        elif 's SATISFIABLE' in statuses:
            status = 'SAT_PENDING_INDEPENDENT_GROUP_REPLAY'
        elif 's UNSATISFIABLE' in statuses:
            status = 'UNSAT_REPORTED_NEEDS_PROOF_AUDIT'
        elif stop or not statuses:
            status = 'BOUNDED_UNKNOWN'
        else:
            status = 'PRODUCER_FAILURE'
        compress(stdout_path, HERE / 'solver.stdout.gz')
        compress(stderr_path, HERE / 'solver.stderr.gz')
        result = {
            'status': status, 'candidate_id': None, 'curve_id': cfg['curve_id'],
            'workload_id': cfg['workload_id'], 'branch_prefix_value': cfg['branch_prefix_value'],
            'formula_sha256': formula_hash, 'formula_bytes': formula.stat().st_size,
            'raw_stdout_sha256': raw_stdout_hash, 'raw_stderr_sha256': raw_stderr_hash,
            'compressed_stdout_sha256': sha(HERE / 'solver.stdout.gz'),
            'compressed_stderr_sha256': sha(HERE / 'solver.stderr.gz'),
            'solver_command': command, 'solver_exit_code': exit_code,
            'stop_reason': stop, 'monitor_error': monitor_error,
            'status_lines': statuses, 'model_line_count': len(model_lines),
            'restart_rows': sum(line.startswith('c rst') for line in lines),
            'rss_samples': samples, 'sampled_peak_combined_rss_bytes': peak,
            'parent_wall_seconds': (time.monotonic_ns() - started) / 1e9,
            'phase_ns': phase, 'protocol_sha256': sha(cfg_path),
            'parent_ru_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
        (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({k: result[k] for k in ('status','parent_wall_seconds','sampled_peak_combined_rss_bytes','restart_rows','status_lines','stop_reason')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
