"""Exhaustive independent GF(2^41) root-pair comparison for indexed hits."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = (1 << 41) | (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return result


def freeze():
    save('pair_audit_protocol.json', {'status': 'FROZEN_EXHAUSTIVE_ROOT_PAIR_AUDIT',
         'source_sha256': {'script': sha(Path(__file__)),
                           'protocol': sha(HERE / 'protocol.json'),
                           'root_table': sha(HERE / 'root_table.json'),
                           'producer_result': sha(HERE / 'result.json')}})


def run():
    frozen = json.loads((HERE / 'pair_audit_protocol.json').read_text())
    assert frozen['source_sha256'] == {
        'script': sha(Path(__file__)), 'protocol': sha(HERE / 'protocol.json'),
        'root_table': sha(HERE / 'root_table.json'),
        'producer_result': sha(HERE / 'result.json')}
    table = json.loads((HERE / 'root_table.json').read_text())['sides']
    producer = json.loads((HERE / 'result.json').read_text())
    assert len(table) == 2 and len(table[0]) == 600 and len(table[1]) == 616
    right = [(row['root'], mul(row['root'], row['root']), row)
             for row in table[1]]
    output = []
    for query in producer['queries']:
        target = query['target_reciprocal']
        t2 = mul(target, target)
        start = time.monotonic_ns()
        hits = []
        comparisons = 0
        for left in table[0]:
            u = left['root']
            ut = mul(u, target)
            A = 1 ^ mul(ut, ut)
            B = ut
            C = t2 ^ mul(u, u)
            for v, v2, row in right:
                comparisons += 1
                if mul(A, v2) ^ mul(B, v) ^ C:
                    continue
                if len(set(left['columns']+row['columns'])) != 8:
                    continue
                hits.append({'left_options': left['options'],
                             'right_options': row['options'],
                             'left_root': u, 'right_root': v})
        elapsed = time.monotonic_ns()-start
        assert comparisons == 369600
        normalize = lambda rows: sorted(json.dumps(row, sort_keys=True) for row in rows)
        assert normalize(hits) == normalize(query['hits']), query['label']
        output.append({'label': query['label'], 'root_pairs_checked': comparisons,
                       'target_hits': len(hits), 'independent_ns': elapsed})
    save('pair_audit_result.json', {'status': 'PASS_EXHAUSTIVE_ROOT_PAIR_AUDIT',
         'candidate_id': None, 'rows': output,
         'total_pairs_checked': sum(row['root_pairs_checked'] for row in output),
         'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'protocol_sha256': sha(HERE / 'pair_audit_protocol.json')})
    print('PASS_EXHAUSTIVE_ROOT_PAIR_AUDIT', output)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
