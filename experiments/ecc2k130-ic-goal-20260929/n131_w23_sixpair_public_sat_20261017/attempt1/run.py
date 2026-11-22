"""Frozen one-worker ordinary N131 W23 six-pair SAT query."""
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_w23_sixpair_shared_circuit_20261017'
N41 = ROOT / 'n41_sixpair_shared_target_20261017'
PUBLIC = ROOT / 'n131_fixed_seed_eight_pair_circuit_20261010' / 'target_preimages.json'
SAGE = HERE.parents[2] / 'sage'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
sys.path.insert(0, str(SOURCE))
import circuit  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def sources():
    paths = {'script': Path(__file__), 'circuit': SOURCE / 'circuit.py',
             'fixture': SOURCE / 'fixture.json',
             'source_protocol': SOURCE / 'protocol_v3.json',
             'source_build': SOURCE / 'result_v3.json',
             'source_verification': SOURCE / 'verification.json',
             'n41_relation': N41 / 'join_audit_result.json',
             'public': PUBLIC, 'runtime': HERE / 'sage_runtime_info.json',
             'solver': SOLVER}
    return {name: sha(path) for name, path in paths.items()}


def freeze():
    assert SAGE.exists() and SOLVER.exists()
    source = json.loads((SOURCE / 'result_v3.json').read_text())
    assert source['status'] == 'COMPLETE'
    assert source['target_public_point'] == json.loads(PUBLIC.read_text())['preimages'][0]['point']
    control = json.loads((N41 / 'join_audit_result.json').read_text())
    assert control['status'].startswith('PASS')
    save('protocol.json', {'status': 'FROZEN_W23_SIXPAIR_PUBLIC_BEFORE_QUERY',
         'curve_id': 'EC1N131Ckb1heb5f1998f20b', 'workload_id': 'cc09e7eb202a',
         'public_target': [1052727368764798954359115163823647684025,
                           2071227447786120917960296877345506689833],
         'raw_preimage_index': 0,
         'raw_point': source['target_public_point'],
         'source': 'W23 canonical seed 898618 six pair rotations 0,18,36,54,72,90',
         'pair_column_policy': 'lazy independent check of any solver model',
         'worker_count': 1, 'target_dependent_cap_seconds': 600,
         'solver_cap_seconds': 580, 'combined_rss_cap_bytes': 4294967296,
         'solver_flags': ['--threads=1', '--maxtime=580', '--zero-exit-status',
                          '--verb=1', '--printsol=1'],
         'source_sha256': sources()})


def decode_model(output, machine, wires):
    lines = [line for line in output.splitlines() if line.startswith('v ')]
    literals = [int(token) for line in lines for token in line.split()[1:]]
    positive = {value for value in literals if value > 0}
    assigned = {abs(value) for value in literals if value}
    assert len(assigned) == machine.next_var - 1
    assert len(assigned) == len(positive) + sum(value < 0 for value in literals)
    def lit_true(lit):
        return lit in positive if lit > 0 else -lit not in positive
    for row in machine.clauses:
        tokens = [int(value) for value in row.split()[:-1]]
        assert any(lit_true(value) for value in tokens)
    for row in machine.xors:
        tokens = [int(value) for value in row.split()[1:-1]]
        assert sum(lit_true(value) for value in tokens) % 2 == 1
    def bits(values):
        return sum((wire in positive) << i for i, wire in enumerate(values))
    codes = [sum(((wire in positive) << circuit.BITS[i])
                 for i, wire in enumerate(slot)) for slot in wires['mask']]
    model = {'status': 'SAT_FORMULA_REPLAY_PASS_GROUP_AUDIT_PENDING',
             'mask_codes': codes,
             'unrotated_pair_standard_reciprocals': [bits(row) for row in wires['out']],
             'middle_standard_reciprocals': [bits(row) for row in wires['middle']],
             'assigned_variables': len(assigned),
             'verified_clauses': len(machine.clauses),
             'verified_xor_rows': len(machine.xors)}
    save('decoded_model.json', model)
    return model


def query():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_W23_SIXPAIR_PUBLIC_BEFORE_QUERY'
    assert protocol['source_sha256'] == sources()
    archived = json.loads(PUBLIC.read_text())['preimages'][0]['point']
    assert archived == protocol['raw_point']
    parent = psutil.Process()
    t0 = time.monotonic_ns()
    target_reciprocal = circuit.F.inverse(archived[0])
    t1 = time.monotonic_ns()
    machine, wires, counts = circuit.build(target_reciprocal, 'shared')
    t2 = time.monotonic_ns()
    formula = HERE / 'ordinary.xcnf'
    machine.write(formula)
    t3 = time.monotonic_ns()
    assert counts['variables'] == 127822 and counts['clauses'] == 263060
    assert counts['xor_rows'] == 38657
    assert t3 - t0 < 20_000_000_000
    print(json.dumps({'stage': 'formula_ready', 'counts': counts,
                      'xcnf_sha256': sha(formula)}), flush=True)
    peak = parent.memory_info().rss
    degraded = False
    stop = None
    command = [str(SOLVER), *protocol['solver_flags'], str(formula)]
    with (HERE / 'solver.stdout').open('x') as stdout, (HERE / 'solver.stderr').open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                total = parent.memory_info().rss + child.memory_info().rss
                peak = max(peak, total)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                degraded = True
                stop = 'MONITOR_FAILURE'
                process.kill()
                break
            if total > protocol['combined_rss_cap_bytes']:
                stop = 'RSS_CAP'
                process.kill()
                break
            if time.monotonic_ns() - t0 >= 595_000_000_000:
                stop = 'TARGET_DEPENDENT_TIMEOUT'
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    t4 = time.monotonic_ns()
    output = (HERE / 'solver.stdout').read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    decoded = None
    if stop:
        status = 'BOUNDED_UNKNOWN' if stop != 'MONITOR_FAILURE' else 'MONITOR_FAILURE'
    elif any(line == 's SATISFIABLE' for line in statuses):
        status = 'SAT_PENDING_GROUP_REPLAY'
        decoded = decode_model(output, machine, wires)
    elif any(line == 's UNSATISFIABLE' for line in statuses):
        status = 'UNSAT_UNVERIFIED'
    else:
        status = 'BOUNDED_UNKNOWN'
    t5 = time.monotonic_ns()
    phase = {'target_conversion_ns': t1-t0,
             'formula_construction_ns': t2-t1,
             'formula_serialization_ns': t3-t2,
             'solver_search_ns': t4-t3,
             'terminal_parse_and_model_check_ns': t5-t4}
    assert sum(phase.values()) == t5-t0
    result = {'status': status, 'candidate_id': None,
              'curve_id': protocol['curve_id'], 'workload_id': protocol['workload_id'],
              'public_target': protocol['public_target'], 'raw_point': archived,
              'raw_preimage_index': 0,
              'target_reciprocal': target_reciprocal,
              'formula_counts': counts, 'formula_bytes': formula.stat().st_size,
              'formula_sha256': sha(formula), 'phase_ns': phase,
              'target_dependent_attempt_ns': t5-t0,
              'worker_count': 1, 'solver_command': command,
              'solver_exit_code': exit_code, 'stop_reason': stop,
              'monitor_degraded': degraded, 'sampled_peak_combined_rss_bytes': peak,
              'parent_ru_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'status_lines': statuses,
              'restart_rows': sum(line.startswith('c rst') for line in output.splitlines()),
              'model_decoded': decoded is not None,
              'solver_stdout_sha256': sha(HERE / 'solver.stdout'),
              'solver_stderr_sha256': sha(HERE / 'solver.stderr'),
              'protocol_sha256': sha(HERE / 'protocol.json')}
    save('result.json', result)
    print(json.dumps({'status': status, 'seconds': (t5-t0)/1e9,
                      'peak_combined_rss_bytes': peak}), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'query')
    {'freeze': freeze, 'query': query}[sys.argv[1]]()
