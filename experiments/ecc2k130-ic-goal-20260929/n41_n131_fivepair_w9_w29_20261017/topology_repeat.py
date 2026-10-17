"""Reverse-order replay of the same fixed-conflict W29 topology screen."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def freeze():
    first = json.loads((HERE / 'topology_protocol.json').read_text())
    result = json.loads((HERE / 'topology_result.json').read_text())
    assert first['status'] == 'FROZEN_W29_FIVEPAIR_TOPOLOGY_CONFLICT_SCREEN'
    assert result['status'] == 'COMPLETE_TOPOLOGY_CONFLICT_SCREEN'
    names = ['topology_protocol.json', 'topology_result.json',
             'n131_ordinary.xcnf', 'n131_3p2.xcnf', 'sage_runtime_info.json']
    save(HERE / 'topology_repeat_protocol.json', {
        'status': 'FROZEN_REVERSE_ORDER_TOPOLOGY_SCREEN',
        'ordered_arms': ['four_plus_one', 'three_plus_two'],
        'formulas': first['formulas'], 'shared_flags': first['shared_flags'],
        'parent_cap_seconds_per_arm': first['parent_cap_seconds_per_arm'],
        'combined_rss_cap_bytes': first['combined_rss_cap_bytes'],
        'source_sha256': {name: sha(HERE / name) for name in names},
        'solver_sha256': sha(SOLVER), 'script_sha256': sha(Path(__file__))})


def run():
    protocol_path = HERE / 'topology_repeat_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_REVERSE_ORDER_TOPOLOGY_SCREEN'
    for name, digest in protocol['source_sha256'].items():
        assert sha(HERE / name) == digest, name
    assert sha(SOLVER) == protocol['solver_sha256']
    assert sha(Path(__file__)) == protocol['script_sha256']
    parent = psutil.Process()
    rows = []
    for name in protocol['ordered_arms']:
        formula = HERE / protocol['formulas'][name]
        command = [str(SOLVER), *protocol['shared_flags'], str(formula)]
        stdout_path = HERE / f'topology_repeat_{name}.stdout'
        stderr_path = HERE / f'topology_repeat_{name}.stderr'
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
               'last_restart': restarts[-1] if restarts else None,
               'formula_sha256': sha(formula),
               'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
        rows.append(row)
        print(json.dumps({'arm': name, 'elapsed_seconds': elapsed / 1e9,
                          'statuses': statuses, 'restarts': len(restarts),
                          'stop_reason': stop}), flush=True)
    save(HERE / 'topology_repeat_result.json', {
        'status': 'COMPLETE_REVERSE_ORDER_TOPOLOGY_SCREEN',
        'candidate_id': None, 'rows': rows,
        'protocol_sha256': sha(protocol_path)})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
