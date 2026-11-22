"""One-worker W9 public query with exact lazy source and column cuts."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
spec = importlib.util.spec_from_file_location('w9_lazy_circuit', HERE / 'circuit.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)
CAP_SECONDS = 180
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    with path.open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def mismatch(wires, code):
    return [(-wire if code >> bit & 1 else wire)
            for bit, wire in enumerate(wires)]


def decode(output, machine, wires):
    literals = [int(token) for line in output.splitlines() if line.startswith('v ')
                for token in line.split()[1:]]
    positive = {lit for lit in literals if lit > 0}
    assigned = {abs(lit) for lit in literals if lit}
    assert len(assigned) == machine.next_var - 1
    def truth(lit):
        return lit in positive if lit > 0 else -lit not in positive
    assert all(any(truth(int(x)) for x in row.split()[:-1])
               for row in machine.clauses)
    assert all(sum(truth(int(x)) for x in row.split()[1:-1]) % 2 == 1
               for row in machine.xors)
    def word(bits):
        return sum((wire in positive) << j for j, wire in enumerate(bits))
    return {'mask_codes': [word(row) for row in wires['mask']],
            'mask_values': [sum((code >> j & 1) << bit
                                for j, bit in enumerate(design.BITS))
                            for code in (word(row) for row in wires['mask'])],
            'output_reciprocals': [word(row) for row in wires['out']],
            'middle_reciprocals': [word(row) for row in wires['middle']],
            'assigned_variables': len(assigned)}


def full_columns(states):
    bymask = {}
    for slot in states['states']:
        for row in slot:
            key = row['masks'][0]
            if key in bymask:
                assert bymask[key] == row['columns']
            bymask[key] = row['columns']
    return bymask


def run(variant):
    assert variant in ('exact5', 'exact3', 'table5')
    fixture = json.loads((HERE / 'fixture.json').read_text())
    screen = json.loads((HERE / 'screen_result.json').read_text())
    states = json.loads(design.SOURCE.read_text())
    bymask = full_columns(states)
    assert fixture['curve_id'] == screen['curve_id'] == states['curve_id']
    source = {path.name: sha(path) for path in
              (Path(__file__), HERE / 'circuit.py', HERE / 'fixture.json',
               HERE / 'screen_result.json', design.SOURCE,
               HERE / (variant + '.xcnf'), SOLVER, HERE / 'sage_runtime_info.json')}
    protocol = HERE / (variant + '_protocol.json')
    save(protocol, {'status': 'FROZEN_BEFORE_PUBLIC_QUERY', 'variant': variant,
                    'oriented_raw_point': fixture['oriented_raw_point'],
                    'source_sha256': source, 'worker_count': 1,
                    'total_cap_seconds': CAP_SECONDS,
                    'combined_rss_cap_bytes': RSS_CAP,
                    'solver_flags': ['--threads=1', '--zero-exit-status',
                                     '--verb=1', '--printsol=1'],
                    'lazy_cut_policy': 'exclude invalid slot codes; exclude code pairs with repeated folded columns'})
    machine, wires, counts = design.build(fixture['oriented_target_reciprocal'], variant)
    assert counts == next(row['counts'] for row in screen['rows'] if row['variant'] == variant)
    assert sha(HERE / (variant + '.xcnf')) == next(
        row['formula_sha256'] for row in screen['rows'] if row['variant'] == variant)
    started = time.monotonic_ns()
    parent = psutil.Process()
    attempts = []
    cuts = []
    peak = parent.memory_info().rss
    status = 'BOUNDED_UNKNOWN'
    model = None
    while True:
        elapsed = (time.monotonic_ns() - started) / 1e9
        remaining = CAP_SECONDS - elapsed
        if remaining < 2:
            break
        index = len(attempts)
        formula = HERE / f'{variant}_attempt{index}.xcnf'
        base = (HERE / (variant + '.xcnf')).read_text()
        header, body = base.split('\n', 1)
        header_parts = header.split()
        header_parts[-1] = str(int(header_parts[-1]) + len(cuts))
        formula.write_text(' '.join(header_parts) + '\n' + body +
                           ''.join(' '.join(map(str, cut)) + ' 0\n' for cut in cuts))
        command = [str(SOLVER), '--threads=1',
                   f'--maxtime={max(1, int(remaining - 1))}',
                   '--zero-exit-status', '--verb=1', '--printsol=1', str(formula)]
        stdout_path = HERE / f'{variant}_attempt{index}.stdout'
        stderr_path = HERE / f'{variant}_attempt{index}.stderr'
        stop = None
        launched = time.monotonic_ns()
        with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    total = parent.memory_info().rss + child.memory_info().rss
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
                if (time.monotonic_ns() - started) / 1e9 >= CAP_SECONDS:
                    stop = 'TIME_CAP'
                    process.kill()
                    break
                time.sleep(0.05)
            exit_code = process.wait()
        ended = time.monotonic_ns()
        output = stdout_path.read_text(errors='replace')
        statuses = [line for line in output.splitlines() if line.startswith('s ')]
        row = {'attempt': index, 'command': command, 'formula_sha256': sha(formula),
               'solver_stdout_sha256': sha(stdout_path),
               'solver_stderr_sha256': sha(stderr_path),
               'solver_elapsed_ns': ended - launched,
               'status_lines': statuses, 'stop_reason': stop,
               'exit_code': exit_code, 'cuts_before': len(cuts)}
        attempts.append(row)
        print(json.dumps(row), flush=True)
        if stop or 's SATISFIABLE' not in statuses:
            if 's UNSATISFIABLE' in statuses:
                status = 'UNSAT_UNVERIFIED'
            elif stop == 'MONITOR_FAILURE':
                status = stop
            break
        model = decode(output, machine, wires)
        values = model['mask_values']
        bad = next((slot for slot, mask in enumerate(values) if mask not in bymask), None)
        if bad is not None:
            cuts.append(mismatch(wires['mask'][bad], model['mask_codes'][bad]))
            row['rejection'] = {'kind': 'INVALID_PAIR_SOURCE', 'slot': bad,
                                'mask': values[bad]}
            continue
        seen = {}
        collision = None
        for slot, mask in enumerate(values):
            for column in bymask[mask]:
                if column in seen:
                    collision = (seen[column], slot, column)
                    break
                seen[column] = slot
            if collision:
                break
        if collision:
            left, right, column = collision
            cuts.append(mismatch(wires['mask'][left], model['mask_codes'][left]) +
                        mismatch(wires['mask'][right], model['mask_codes'][right]))
            row['rejection'] = {'kind': 'FOLDED_COLUMN_COLLISION',
                                'slots': [left, right], 'column': column}
            continue
        status = 'SAT_MEMBERSHIP_PASS_GROUP_AUDIT_PENDING'
        break
    ended = time.monotonic_ns()
    result = {'status': status, 'variant': variant,
              'curve_id': fixture['curve_id'],
              'oriented_raw_point': fixture['oriented_raw_point'],
              'formula_counts': counts, 'attempts': attempts,
              'cuts': cuts, 'last_model': model,
              'total_query_ns': ended - started,
              'sampled_peak_combined_rss_bytes': peak,
              'protocol_sha256': sha(protocol)}
    save(HERE / (variant + '_result.json'), result)
    print(json.dumps({'variant': variant, 'status': status,
                      'seconds': (ended - started) / 1e9,
                      'attempt_count': len(attempts), 'cut_count': len(cuts),
                      'peak_rss_bytes': peak}), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    run(sys.argv[1])
