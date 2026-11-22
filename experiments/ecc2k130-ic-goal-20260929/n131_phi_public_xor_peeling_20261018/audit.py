"""Independently reverse-solve and verify the full XOR peel certificate."""
from collections import defaultdict
import hashlib
import json
import random
import resource
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'audit_protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for label, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], label
    producer = json.loads((HERE / 'result.json').read_text())
    assert producer['peeled_rows'] == producer['native_xor_rows'] == 208783
    interface = set(cfg['interface_variables'])
    start = time.monotonic()
    variables = []
    rhs = []
    incidence = defaultdict(list)
    degrees = defaultdict(int)
    with Path(cfg['sources']['formula']['path']).open('rb') as stream:
        header = stream.readline().split()
        assert header[:2] == [b'p', b'cnf'] and len(header) == 4
        nvars = int(header[2])
        for line in stream:
            if not line.startswith(b'x'):
                continue
            fields = [int(token) for token in line[1:].split()]
            assert fields[-1] == 0 and len(fields) > 1
            signed = fields[:-1]
            row = len(variables)
            variables.append(tuple(abs(v) for v in signed))
            rhs.append(1 ^ (sum(v < 0 for v in signed) & 1))
            for v in signed:
                key = abs(v)
                if key not in interface:
                    incidence[key].append(row)
                    degrees[key] += 1
    assert len(variables) == producer['native_xor_rows']
    active = bytearray(b'\x01') * len(variables)
    stack = [v for v, degree in degrees.items() if degree == 1]
    order = []
    while stack:
        pivot = stack.pop()
        if degrees[pivot] != 1:
            continue
        live = next((row for row in incidence[pivot] if active[row]), None)
        assert live is not None
        active[live] = 0
        order.append((live, pivot))
        for member in variables[live]:
            if member not in interface:
                degrees[member] -= 1
                if degrees[member] == 1:
                    stack.append(member)
    assert len(order) == len(variables) and not any(active)
    digest = hashlib.sha256()
    for row, pivot in order:
        digest.update(struct.pack('<II', row, pivot))
    replay_seeds = [41018, 131018, 20261018]
    for seed in replay_seeds:
        rng = random.Random(seed)
        value = bytearray(nvars + 1)
        value[1] = 1
        for v in sorted(interface - {1}):
            value[v] = rng.randrange(2)
        for row, pivot in reversed(order):
            bit = rhs[row]
            for v in variables[row]:
                if v != pivot:
                    bit ^= value[v]
            value[pivot] = bit
        for row, members in enumerate(variables):
            parity = 0
            for v in members:
                parity ^= value[v]
            assert parity == rhs[row], (seed, row)
    result = {'status': 'PASS_INDEPENDENT_FULL_XOR_PEEL_AND_REVERSE_REPLAY',
              'formula_sha256': cfg['sources']['formula']['sha256'],
              'producer_result_sha256': sha(HERE / 'result.json'),
              'audit_protocol_sha256': sha(cfg_path),
              'interface_variables': sorted(interface),
              'rows': len(variables), 'peeled_rows': len(order),
              'pivot_sequence_sha256': digest.hexdigest(),
              'interface_assignment_seeds': replay_seeds,
              'full_xor_replay_passes': len(replay_seeds),
              'wall_seconds': time.monotonic() - start,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE / 'audit_result.json').open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'peeled_rows',
                                             'full_xor_replay_passes',
                                             'wall_seconds', 'peak_rss_bytes')}, sort_keys=True))


if __name__ == '__main__':
    main()
