"""Independent exclusive-pivot certificate for public XOR rows."""
from collections import Counter
import hashlib
import json
import resource
import sys
from pathlib import Path

import code_only
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
            'first_screen': HERE / 'result.json'}


def freeze():
    save('leaf_protocol.json', {'status': 'FROZEN_EXCLUSIVE_XOR_PIVOT_AUDIT',
        'source_sha256': {k: sha(v) for k, v in inputs().items()}})


def rows(path):
    with path.open() as source:
        for line in source:
            if line.startswith('x'):
                literals = [int(x) for x in line[1:].split()[:-1]]
                yield {abs(x) for x in literals}


def run():
    protocol = json.loads((HERE / 'leaf_protocol.json').read_text())
    assert protocol['source_sha256'] == {k: sha(v) for k, v in inputs().items()}
    prior = json.loads((HERE / 'code_result.json').read_text())
    out = []
    for label, path in [('n41', screen.N41 / 'public.xcnf'),
                        ('n131', screen.N131 / 'ordinary.xcnf')]:
        count, code = code_only.code_wires(label)
        data = list(rows(path))
        degree = Counter(v for row in data for v in row)
        pivots = []
        for row in data:
            candidates = [v for v in row if v not in code and degree[v] == 1]
            assert candidates
            pivots.append(min(candidates))
        assert len(set(pivots)) == len(data)
        old = next(r for r in prior['rows'] if r['label'] == label)
        assert len(data) == old['private_pivots']
        assert old['code_only_xor_rows'] == 0
        out.append({'label': label, 'xor_rows': len(data),
            'exclusive_noncode_pivots': len(pivots),
            'pivot_list_sha256': hashlib.sha256(json.dumps(pivots).encode()).hexdigest(),
            'code_wires': len(code), 'variables': count,
            'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        print(label, len(pivots), flush=True)
    save('leaf_result.json', {'status': 'PASS_EXCLUSIVE_XOR_PIVOT_AUDIT',
        'protocol_sha256': sha(HERE / 'leaf_protocol.json'), 'rows': out})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
