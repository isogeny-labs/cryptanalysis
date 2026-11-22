"""Capped public N131 query with the checked global output-trace constraint."""
import hashlib
import importlib.util
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_fivepair_w9_w29_20261017'
PUBLIC = ROOT / 'n131_w23_sixpair_public_sat_20261017/protocol.json'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')
spec = importlib.util.spec_from_file_location('w29_trace_query', PRIOR / 'circuit_n131_3p2.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def sources():
    paths = {'runner': Path(__file__), 'circuit': PRIOR / 'circuit_n131_3p2.py',
             'previous_circuit': Path(design.previous.__file__),
             'public': PUBLIC,
             'control': PRIOR / 'n131_control_3p2.json',
             'control_check': HERE / 'build_n131_result.json',
             'trace_census': HERE / 'census_trace_result.json',
             'proof': HERE / 'TraceParity.lean',
             'proof_stdout': HERE / 'lean.stdout',
             'formula': HERE / 'n131_trace.xcnf',
             'runtime': HERE / 'sage_runtime_info.json',
             'solver': SOLVER}
    return {name: sha(path) for name, path in paths.items()}


def freeze():
    public = json.loads(PUBLIC.read_text())
    check = json.loads((HERE / 'build_n131_result.json').read_text())
    assert check['status'] == 'PASS_N131_TRACE_GATE_CONSTRUCTED_ASSIGNMENT'
    assert check['curve_id'] == public['curve_id']
    assert check['trace_sha256'] == sha(HERE / 'n131_trace.xcnf')
    save('n131_trace_query_protocol.json', {
        'status': 'FROZEN_N131_W29_FIVEPAIR_TRACE_PUBLIC_BEFORE_QUERY',
        'curve_id': public['curve_id'], 'workload_id': public['workload_id'],
        'public_target': public['public_target'], 'raw_point': public['raw_point'],
        'raw_preimage_index': public['raw_preimage_index'],
        'candidate_id': None, 'worker_count': 1,
        'target_dependent_cap_seconds': 600,
        'solver_cap_seconds': 580,
        'combined_rss_cap_bytes': 4 * 1024**3,
        'solver_flags': ['--threads=1', '--maxtime=580', '--zero-exit-status',
                         '--verb=1', '--printsol=1'],
        'source_sha256': sources()})


def decode_model(output, circuit, wires):
    lines = [line for line in output.splitlines() if line.startswith('v ')]
    literals = [int(token) for line in lines for token in line.split()[1:]]
    positive = {lit for lit in literals if lit > 0}
    assigned = {abs(lit) for lit in literals if lit}
    assert len(assigned) == circuit.next_var - 1
    def truth(lit):
        return lit in positive if lit > 0 else -lit not in positive
    for row in circuit.clauses:
        assert any(truth(int(token)) for token in row.split()[:-1])
    for row in circuit.xors:
        assert sum(truth(int(token)) for token in row.split()[1:-1]) % 2 == 1
    def bits(values):
        return sum((wire in positive) << i for i, wire in enumerate(values))
    model = {'status': 'SAT_FORMULA_REPLAY_PASS_GROUP_AUDIT_PENDING',
             'mask_codes': [sum(((wire in positive) << design.BITS[i])
                                for i, wire in enumerate(slot)) for slot in wires['mask']],
             'unrotated_pair_standard_reciprocals': [bits(row) for row in wires['out']],
             'middle_standard_reciprocals': [bits(row) for row in wires['middle']],
             'assigned_variables': len(assigned),
             'verified_clauses': len(circuit.clauses),
             'verified_xor_rows': len(circuit.xors)}
    save('n131_trace_decoded_model.json', model)
    return model


def query():
    protocol_path = HERE / 'n131_trace_query_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_N131_W29_FIVEPAIR_TRACE_PUBLIC_BEFORE_QUERY'
    assert protocol['source_sha256'] == sources()
    parent = psutil.Process()
    start = time.monotonic_ns()
    reciprocal = design.F.inverse(protocol['raw_point'][0])
    converted = time.monotonic_ns()
    circuit, wires, counts = design.build(reciprocal)
    built = time.monotonic_ns()
    assert counts['and_gates'] == 76859 and counts['variables'] == 121204
    assert counts['clauses'] == 232429 and counts['xor_rows'] == 42502
    trace_wires = [wire for row in wires['out']
                   for wire, tr in zip(row, design.TRACE) if tr]
    target_trace = design.previous.trace(reciprocal)
    circuit.require_zero([circuit.xor(trace_wires + ([-1] if target_trace else []))])
    assert len(trace_wires) == 10
    assert len(circuit.clauses) == 232430 and len(circuit.xors) == 42503
    formula = HERE / 'n131_trace_query.xcnf'
    circuit.write(formula)
    assert sha(formula) == protocol['source_sha256']['formula']
    serialized = time.monotonic_ns()
    print(json.dumps({'stage': 'formula_ready', 'xcnf_sha256': sha(formula),
                      'build_seconds': (serialized - start) / 1e9}), flush=True)
    peak = parent.memory_info().rss
    stop = None
    command = [str(SOLVER), *protocol['solver_flags'], str(formula)]
    with (HERE / 'n131_trace_solver.stdout').open('x') as stdout, \
         (HERE / 'n131_trace_solver.stderr').open('x') as stderr:
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
    output_path = HERE / 'n131_trace_solver.stdout'
    output = output_path.read_text(errors='replace')
    statuses = [line for line in output.splitlines() if line.startswith('s ')]
    if stop:
        status = 'MONITOR_FAILURE' if stop == 'MONITOR_FAILURE' else 'BOUNDED_UNKNOWN'
    elif 's SATISFIABLE' in statuses:
        status = 'SAT_PENDING_GROUP_REPLAY'
        decode_model(output, circuit, wires)
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
              'target_reciprocal': reciprocal, 'target_trace': target_trace,
              'formula_sha256': sha(formula), 'formula_bytes': formula.stat().st_size,
              'phase_ns': phases, 'target_dependent_attempt_ns': checked - start,
              'worker_count': 1, 'solver_command': command, 'solver_exit_code': exit_code,
              'stop_reason': stop, 'sampled_peak_combined_rss_bytes': peak,
              'parent_ru_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'status_lines': statuses,
              'model_decoded': status == 'SAT_PENDING_GROUP_REPLAY',
              'solver_stdout_sha256': sha(output_path),
              'solver_stderr_sha256': sha(HERE / 'n131_trace_solver.stderr'),
              'protocol_sha256': sha(protocol_path)}
    save('n131_trace_query_result.json', result)
    print(json.dumps({'status': status, 'seconds': (checked - start) / 1e9,
                      'peak_combined_rss_bytes': peak}), flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'query')
    {'freeze': freeze, 'query': query}[sys.argv[1]]()
