"""Frozen one-worker balanced W29 five-pair query on the N131 public point."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def sources():
    paths = {'runner': Path(__file__), 'circuit': HERE / 'circuit_n131_3p2.py',
             'previous_circuit': Path(design.previous.__file__),
             'control': HERE / 'n131_control_3p2.json',
             'control_screen': HERE / 'n131_circuit_result_3p2.json',
             'n41_relation': HERE / 'orbit_audit_result.json',
             'w29_sample': HERE / 'sample_result.json',
             'w29_sample_audit': HERE / 'sample_audit_result.json',
             'topology_audit': HERE / 'topology_audit_result.json',
             'public': PUBLIC, 'runtime': HERE / 'sage_runtime_info.json',
             'solver': SOLVER}
    return {name: sha(path) for name, path in paths.items()}


def freeze():
    public = json.loads(PUBLIC.read_text())
    control = json.loads((HERE / 'n131_circuit_result_3p2.json').read_text())
    relation = json.loads((HERE / 'orbit_audit_result.json').read_text())
    sample = json.loads((HERE / 'sample_result.json').read_text())
    assert control['status'] == 'COMPLETE_CIRCUIT_SCREEN'
    assert relation['status'] == 'PASS_INDEPENDENT_N41_W9_FIVEPAIR_PUBLIC_RELATION'
    assert sample['status'] == 'COMPLETE'
    assert public['curve_id'] == control['curve_id']
    assert control['public_point'] == public['public_target']
    save('n131_query_protocol_3p2.json', {
        'status': 'FROZEN_W29_FIVEPAIR_3P2_PUBLIC_BEFORE_QUERY',
        'curve_id': public['curve_id'], 'workload_id': public['workload_id'],
        'public_target': public['public_target'], 'raw_point': public['raw_point'],
        'raw_preimage_index': public['raw_preimage_index'],
        'source': 'W29 canonical fixed-seed 898618; five pairs; rotations 0,18,36,54,72; three-plus-two links',
        'pair_column_policy': 'lazy independent check of any solver model',
        'worker_count': 1, 'target_dependent_cap_seconds': 600,
        'solver_cap_seconds': 580, 'combined_rss_cap_bytes': 4 * 1024**3,
        'solver_flags': ['--threads=1', '--maxtime=580', '--zero-exit-status',
                         '--verb=1', '--printsol=1'],
        'source_sha256': sources()})


def decode_model(output, machine, wires):
    lines = [line for line in output.splitlines() if line.startswith('v ')]
    literals = [int(token) for line in lines for token in line.split()[1:]]
    positive = {lit for lit in literals if lit > 0}
    assigned = {abs(lit) for lit in literals if lit}
    assert len(assigned) == machine.next_var - 1
    def truth(lit):
        return lit in positive if lit > 0 else -lit not in positive
    for row in machine.clauses:
        assert any(truth(int(token)) for token in row.split()[:-1])
    for row in machine.xors:
        assert sum(truth(int(token)) for token in row.split()[1:-1]) % 2 == 1
    def bits(values):
        return sum((wire in positive) << i for i, wire in enumerate(values))
    model = {'status': 'SAT_FORMULA_REPLAY_PASS_GROUP_AUDIT_PENDING',
             'mask_codes': [sum(((wire in positive) << design.BITS[i])
                                for i, wire in enumerate(slot)) for slot in wires['mask']],
             'unrotated_pair_standard_reciprocals': [bits(row) for row in wires['out']],
             'middle_standard_reciprocals': [bits(row) for row in wires['middle']],
             'assigned_variables': len(assigned),
             'verified_clauses': len(machine.clauses),
             'verified_xor_rows': len(machine.xors)}
    save('n131_decoded_model_3p2.json', model)
    return model


def query():
    protocol_path = HERE / 'n131_query_protocol_3p2.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_W29_FIVEPAIR_3P2_PUBLIC_BEFORE_QUERY'
    assert protocol['source_sha256'] == sources()
    parent = psutil.Process()
    start = time.monotonic_ns()
    reciprocal = design.F.inverse(protocol['raw_point'][0])
    converted = time.monotonic_ns()
    machine, wires, counts = design.build(reciprocal)
    built = time.monotonic_ns()
    assert counts['and_gates'] == 76859 and counts['variables'] == 121204
    assert counts['clauses'] == 232429 and counts['xor_rows'] == 42502
    formula = HERE / 'n131_3p2_ordinary.xcnf'
    machine.write(formula)
    assert sha(formula) == json.loads((HERE / 'topology_protocol.json').read_text())['source_sha256']['n131_3p2.xcnf']
    serialized = time.monotonic_ns()
    if (serialized - start) / 1e9 > 595:
        raise TimeoutError('target-dependent cap before solver launch')
    print(json.dumps({'stage': 'formula_ready', 'counts': counts,
                      'xcnf_sha256': sha(formula)}), flush=True)
    peak = parent.memory_info().rss
    degraded = False
    stop = None
    command = [str(SOLVER), *protocol['solver_flags'], str(formula)]
    with (HERE / 'n131_3p2_solver.stdout').open('x') as stdout, \
         (HERE / 'n131_3p2_solver.stderr').open('x') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                total = parent.memory_info().rss + child.memory_info().rss
                peak = max(peak, total)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                degraded = True
                stop = 'MONITOR_FAILURE'
                process.kill()
                break
            if total > protocol['combined_rss_cap_bytes']:
                stop = 'RSS_CAP'
                process.kill()
                break
            if (time.monotonic_ns() - start) / 1e9 >= 595:
                stop = 'TARGET_DEPENDENT_TIMEOUT'
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    searched = time.monotonic_ns()
    output = (HERE / 'n131_3p2_solver.stdout').read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    decoded = None
    if stop:
        status = 'BOUNDED_UNKNOWN' if stop != 'MONITOR_FAILURE' else 'MONITOR_FAILURE'
    elif 's SATISFIABLE' in statuses:
        status = 'SAT_PENDING_GROUP_REPLAY'
        decoded = decode_model(output, machine, wires)
    elif 's UNSATISFIABLE' in statuses:
        status = 'UNSAT_UNVERIFIED'
    else:
        status = 'BOUNDED_UNKNOWN'
    checked = time.monotonic_ns()
    phases = {'target_conversion_ns': converted - start,
              'formula_construction_ns': built - converted,
              'formula_serialization_ns': serialized - built,
              'solver_search_ns': searched - serialized,
              'terminal_parse_and_model_check_ns': checked - searched}
    assert sum(phases.values()) == checked - start
    result = {'status': status, 'candidate_id': None,
              'curve_id': protocol['curve_id'], 'workload_id': protocol['workload_id'],
              'public_target': protocol['public_target'], 'raw_point': protocol['raw_point'],
              'raw_preimage_index': protocol['raw_preimage_index'],
              'target_reciprocal': reciprocal,
              'formula_counts': counts, 'formula_bytes': formula.stat().st_size,
              'formula_sha256': sha(formula), 'phase_ns': phases,
              'target_dependent_attempt_ns': checked - start,
              'worker_count': 1, 'solver_command': command,
              'solver_exit_code': exit_code, 'stop_reason': stop,
              'monitor_degraded': degraded, 'sampled_peak_combined_rss_bytes': peak,
              'parent_ru_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'status_lines': statuses,
              'restart_rows': sum(line.startswith('c rst') for line in output.splitlines()),
              'model_decoded': decoded is not None,
              'solver_stdout_sha256': sha(HERE / 'n131_3p2_solver.stdout'),
              'solver_stderr_sha256': sha(HERE / 'n131_3p2_solver.stderr'),
              'protocol_sha256': sha(protocol_path)}
    save('n131_query_result_3p2.json', result)
    print(json.dumps({'status': status, 'seconds': (checked - start) / 1e9,
                      'peak_combined_rss_bytes': peak}), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'query')
    {'freeze': freeze, 'query': query}[sys.argv[1]]()
