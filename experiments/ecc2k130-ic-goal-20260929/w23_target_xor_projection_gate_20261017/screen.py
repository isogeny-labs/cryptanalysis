"""Screen exact public XCNF projection for code-only target constraints."""
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41 = ROOT / 'n41_sixpair_shared_target_20261017'
N131 = ROOT / 'n131_w23_sixpair_public_sat_20261017'
N131_SOURCE = ROOT / 'n131_w23_sixpair_shared_circuit_20261017'
PROJECT = ROOT / 'xor_projection_20261009/project_xcnf.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, record):
    with (HERE / name).open('x') as out:
        json.dump(record, out, indent=2, sort_keys=True)
        out.write('\n')


def sources():
    return {'script': Path(__file__), 'projector': PROJECT,
            'n41_xcnf': N41 / 'public.xcnf',
            'n41_circuit': N41 / 'circuit.py',
            'n41_protocol': N41 / 'protocol.json',
            'n41_build': N41 / 'build_result.json',
            'n131_xcnf': N131 / 'ordinary.xcnf',
            'n131_circuit': N131_SOURCE / 'circuit.py',
            'n131_result': N131 / 'result.json'}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze():
    save('protocol.json', {'status': 'FROZEN_N41_N131_PUBLIC_XOR_CODE_PROJECTION',
        'candidate_id': None, 'one_worker': True,
        'wall_cap_seconds': 180, 'rss_observational_cap_bytes': 4*1024**3,
        'source_sha256': {k: sha(v) for k, v in sources().items()}})


def screen(label, xcnf, circuit, target, projector):
    started = time.monotonic_ns()
    if label == 'n41':
        machine, wires, _ = circuit.build(target)
        code_wires = {v for row in wires['codes'] for v in row}
    else:
        machine, wires, _ = circuit.build(target, 'shared')
        code_wires = {v for row in wires['mask'] for v in row}
    rebuilt = HERE / f'rebuilt_{label}.xcnf'
    machine.write(rebuilt)
    assert sha(rebuilt) == sha(xcnf)
    built_ns = time.monotonic_ns() - started
    nvars, clauses, cnf_used, rows, rhs = projector.scan(xcnf)
    assert nvars == machine.next_var - 1
    original_xors = len(rows)
    pivots, free_private, additions, widest = projector.project(cnf_used, rows, rhs)
    code_only = [(tuple(sorted(row)), rhs[i]) for i, row in rows.items()
                 if row and row <= code_wires]
    result = {'label': label, 'status': 'COMPLETE',
        'rebuilt_sha256': sha(rebuilt), 'code_wires': len(code_wires),
        'original_variables': nvars, 'original_cnf_clauses': clauses,
        'original_xor_rows': original_xors,
        'private_pivots': len(pivots), 'free_private_variables': len(free_private),
        'residual_xor_rows': sum(bool(row) for row in rows.values()),
        'residual_contradictions': sum(not row and rhs[i] for i, row in rows.items()),
        'code_touching_residual_rows': sum(bool(row & code_wires) for row in rows.values()),
        'code_only_residual_rows': len(code_only),
        'code_only_rows_sha256': hashlib.sha256(json.dumps(sorted(code_only)).encode()).hexdigest(),
        'widest_intermediate_row': widest, 'row_additions': additions,
        'rebuild_ns': built_ns, 'total_ns': time.monotonic_ns()-started,
        'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    print(label, result['residual_xor_rows'], result['code_only_residual_rows'], flush=True)
    return result


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['source_sha256'] == {k: sha(v) for k, v in sources().items()}
    signal.alarm(protocol['wall_cap_seconds'])
    projector = load_module('xor_projector', PROJECT)
    n41c = load_module('n41_public_circuit', N41 / 'circuit.py')
    n41_protocol = json.loads((N41 / 'protocol.json').read_text())
    n41_target = n41c.F.inv(n41_protocol['public_raw_point'][0])
    n131c = load_module('n131_public_circuit', N131_SOURCE / 'circuit.py')
    n131_target = json.loads((N131 / 'result.json').read_text())['target_reciprocal']
    results = [screen('n41', N41 / 'public.xcnf', n41c, n41_target, projector),
               screen('n131', N131 / 'ordinary.xcnf', n131c, n131_target, projector)]
    signal.alarm(0)
    assert all(row['peak_self_rss_raw'] < protocol['rss_observational_cap_bytes']
               for row in results)
    save('result.json', {'status': 'PASS_N41_N131_XOR_CODE_PROJECTION_SCREEN',
        'protocol_sha256': sha(HERE / 'protocol.json'), 'rows': results})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
