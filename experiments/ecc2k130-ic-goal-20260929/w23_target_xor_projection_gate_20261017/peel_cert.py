"""Independent ordered leaf-peeling certificate for public XOR rows."""
from collections import defaultdict
import hashlib
import heapq
import json
import resource
import sys
from pathlib import Path

import code_only
import leaf_cert
import screen

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, obj):
    with (HERE / name).open('x') as out:
        json.dump(obj, out, indent=2, sort_keys=True)
        out.write('\n')


def inputs():
    return {'script': Path(__file__), 'n41_xcnf': screen.N41 / 'public.xcnf',
            'n131_xcnf': screen.N131 / 'ordinary.xcnf',
            'code_screen': HERE / 'code_result.json',
            'code_source': HERE / 'code_only.py',
            'first_screen': HERE / 'result.json',
            'failed_static_attempt': HERE / 'leaf_attempt1.json'}


def freeze():
    save('peel_protocol.json', {'status': 'FROZEN_ORDERED_XOR_PEEL_AUDIT',
        'source_sha256': {k: sha(v) for k, v in inputs().items()},
        'one_worker': True, 'rss_observational_cap_bytes': 4*1024**3})


def peel(data, code):
    incidence = defaultdict(set)
    for i, row in enumerate(data):
        for v in row-code:
            incidence[v].add(i)
    initial_leaves = sum(len(members) == 1 for members in incidence.values())
    heap = [v for v, members in incidence.items() if len(members) == 1]
    heapq.heapify(heap)
    active = set(range(len(data)))
    pivots = []
    while heap:
        v = heapq.heappop(heap)
        members = incidence[v]
        if len(members) != 1:
            continue
        row_id = next(iter(members))
        if row_id not in active:
            continue
        assert v not in code and v in data[row_id]
        pivots.append((row_id, v))
        active.remove(row_id)
        for w in data[row_id]-code:
            incidence[w].remove(row_id)
            if len(incidence[w]) == 1:
                heapq.heappush(heap, w)
    return pivots, len(active), initial_leaves


def run():
    protocol = json.loads((HERE / 'peel_protocol.json').read_text())
    assert protocol['source_sha256'] == {k: sha(v) for k, v in inputs().items()}
    out = []
    for label, path in [('n41', screen.N41 / 'public.xcnf'),
                        ('n131', screen.N131 / 'ordinary.xcnf')]:
        nvars, code = code_only.code_wires(label)
        data = list(leaf_cert.rows(path))
        assert all(all(1 <= v <= nvars for v in row) for row in data)
        pivots, remaining, initial = peel(data, code)
        assert not remaining and len(pivots) == len(data)
        assert len({v for _, v in pivots}) == len(data)
        out.append({'label': label, 'xor_rows': len(data),
            'initial_degree_one_noncode_variables': initial,
            'ordered_exclusive_pivots': len(pivots),
            'unpeeled_rows': remaining,
            'pivot_sequence_sha256': hashlib.sha256(json.dumps(pivots).encode()).hexdigest(),
            'code_wires': len(code),
            'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        print(label, len(pivots), initial, flush=True)
    assert all(row['peak_self_rss_raw'] < protocol['rss_observational_cap_bytes']
               for row in out)
    save('peel_result.json', {'status': 'PASS_ORDERED_XOR_PEEL_AUDIT',
        'protocol_sha256': sha(HERE / 'peel_protocol.json'), 'rows': out})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
