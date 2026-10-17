"""Frozen matched-conflict W29 four-plus-one versus three-plus-two screen."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
import circuit_n131_3p2 as balanced


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def sources():
    names = ['circuit_n131.py', 'circuit_n131_3p2.py',
             'n131_circuit_result.json', 'n131_circuit_result_3p2.json',
             'n131_query_result.json', 'orbit_audit_result.json',
             'sample_audit_result.json', 'sage_runtime_info.json',
             'n131_ordinary.xcnf', 'n131_3p2.xcnf']
    result = {name: sha(HERE / name) for name in names}
    result.update({'probe': sha(Path(__file__)), 'solver': sha(SOLVER),
                   'public': sha(PUBLIC)})
    return result


def freeze():
    public = json.loads(PUBLIC.read_text())
    previous = json.loads((HERE / 'n131_query_result.json').read_text())
    assert previous['status'] == 'BOUNDED_UNKNOWN'
    assert previous['formula_sha256'] == sha(HERE / 'n131_ordinary.xcnf')
    reciprocal = balanced.F.inverse(public['raw_point'][0])
    machine, _, counts = balanced.build(reciprocal)
    assert counts == previous['formula_counts']
    balanced_path = HERE / 'n131_3p2.xcnf'
    machine.write(balanced_path)
    save(HERE / 'topology_protocol.json', {
        'status': 'FROZEN_W29_FIVEPAIR_TOPOLOGY_CONFLICT_SCREEN',
        'curve_id': previous['curve_id'], 'workload_id': previous['workload_id'],
        'raw_public_point': previous['raw_point'],
        'ordered_arms': ['three_plus_two', 'four_plus_one'],
        'formulas': {'three_plus_two': 'n131_3p2.xcnf',
                     'four_plus_one': 'n131_ordinary.xcnf'},
        'shared_flags': ['--threads=1', '--maxconfl=100000', '--maxtime=100',
                         '--zero-exit-status', '--verb=1', '--printsol=1'],
        'worker_count': 1, 'parent_cap_seconds_per_arm': 110,
        'combined_rss_cap_bytes': 4 * 1024**3,
        'source_sha256': sources()})
    print(json.dumps({'status': 'FROZEN', 'formula_sha256': sha(balanced_path),
                      'counts': counts}), flush=True)


def run():
    protocol_path = HERE / 'topology_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_W29_FIVEPAIR_TOPOLOGY_CONFLICT_SCREEN'
    assert protocol['source_sha256'] == sources()
    parent = psutil.Process()
    rows = []
    for name in protocol['ordered_arms']:
        formula = HERE / protocol['formulas'][name]
        command = [str(SOLVER), *protocol['shared_flags'], str(formula)]
        stdout_path = HERE / f'topology_{name}.stdout'
        stderr_path = HERE / f'topology_{name}.stderr'
        start = time.monotonic_ns()
        peak = parent.memory_info().rss
        stop = None
        with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    combined = parent.memory_info().rss + child.memory_info().rss
                    peak = max(peak, combined)
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                    stop = 'MONITOR_FAILURE'
                    process.kill()
                    break
                if combined > protocol['combined_rss_cap_bytes']:
                    stop = 'RSS_CAP'
                    process.kill()
                    break
                if (time.monotonic_ns() - start) / 1e9 >= protocol['parent_cap_seconds_per_arm']:
                    stop = 'PARENT_CAP'
                    process.kill()
                    break
                time.sleep(0.05)
            exit_code = process.wait()
        elapsed = time.monotonic_ns() - start
        lines = stdout_path.read_text(errors='replace').splitlines()
        restarts = [line for line in lines if line.startswith('c rst')]
        statuses = [line for line in lines if line.startswith('s ')]
        row = {'arm': name, 'command': command, 'exit_code': exit_code,
               'stop_reason': stop, 'status_lines': statuses,
               'elapsed_ns': elapsed, 'sampled_peak_combined_rss_bytes': peak,
               'restart_count': len(restarts),
               'first_restart': restarts[0] if restarts else None,
               'last_restart': restarts[-1] if restarts else None,
               'formula_sha256': sha(formula),
               'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
        rows.append(row)
        print(json.dumps({'arm': name, 'elapsed_seconds': elapsed / 1e9,
                          'statuses': statuses, 'restarts': len(restarts),
                          'stop_reason': stop}), flush=True)
    save(HERE / 'topology_result.json', {
        'status': 'COMPLETE_TOPOLOGY_CONFLICT_SCREEN',
        'candidate_id': None, 'rows': rows,
        'protocol_sha256': sha(protocol_path),
        'source_sha256': protocol['source_sha256']})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
