"""Eliminate every non-code variable from XOR rows to find code consequences."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

import screen

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, record):
    with (HERE / name).open('x') as out:
        json.dump(record, out, indent=2, sort_keys=True)
        out.write('\n')


def sources():
    paths = screen.sources()
    paths.update({'script': Path(__file__), 'first_screen': HERE / 'result.json',
                  'first_screen_source': HERE / 'screen.py'})
    return {name: sha(path) for name, path in paths.items()}


def freeze():
    save('code_protocol.json', {'status': 'FROZEN_CODE_BOUNDARY_XOR_ELIMINATION',
        'source_sha256': sources(), 'one_worker': True,
        'wall_cap_seconds': 180, 'rss_observational_cap_bytes': 4*1024**3})


def code_wires(label):
    if label == 'n41':
        module = screen.load_module('n41_code_circuit', screen.N41 / 'circuit.py')
        p = json.loads((screen.N41 / 'protocol.json').read_text())
        machine, wires, _ = module.build(module.F.inv(p['public_raw_point'][0]))
        return machine.next_var-1, {v for row in wires['codes'] for v in row}
    module = screen.load_module('n131_code_circuit', screen.N131_SOURCE / 'circuit.py')
    p = json.loads((screen.N131 / 'result.json').read_text())
    machine, wires, _ = module.build(p['target_reciprocal'], 'shared')
    return machine.next_var-1, {v for row in wires['mask'] for v in row}


def run():
    protocol = json.loads((HERE / 'code_protocol.json').read_text())
    assert protocol['source_sha256'] == sources()
    signal.alarm(protocol['wall_cap_seconds'])
    projector = screen.load_module('xor_projector_code', screen.PROJECT)
    rows_out = []
    for label, source in [('n41', screen.N41 / 'public.xcnf'),
                          ('n131', screen.N131 / 'ordinary.xcnf')]:
        started = time.monotonic_ns()
        count, code = code_wires(label)
        nvars, clauses, _, rows, rhs = projector.scan(source)
        assert nvars == count
        keep = bytearray(nvars+1)
        for v in code:
            keep[v] = 1
        pivots, free_private, additions, widest = projector.project(keep, rows, rhs)
        residual = [(tuple(sorted(row)), rhs[i]) for i, row in rows.items() if row]
        assert all(set(row) <= code for row, _ in residual)
        item = {'label': label, 'status': 'COMPLETE', 'code_wires': len(code),
            'code_only_xor_rows': len(residual),
            'code_only_rows_sha256': hashlib.sha256(json.dumps(sorted(residual)).encode()).hexdigest(),
            'contradictions': sum(not row and rhs[i] for i, row in rows.items()),
            'private_pivots': len(pivots), 'free_private': len(free_private),
            'row_additions': additions, 'widest_intermediate_row': widest,
            'elapsed_ns': time.monotonic_ns()-started,
            'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        rows_out.append(item)
        print(label, item['code_only_xor_rows'], item['contradictions'], flush=True)
    signal.alarm(0)
    assert all(row['peak_self_rss_raw'] < protocol['rss_observational_cap_bytes']
               for row in rows_out)
    save('code_result.json', {'status': 'PASS_CODE_BOUNDARY_XOR_ELIMINATION',
        'protocol_sha256': sha(HERE / 'code_protocol.json'), 'rows': rows_out})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
