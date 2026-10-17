"""Precompute two-slot roots and invert the public S3 equation into an index."""
import hashlib
import itertools
import json
import resource
import time
from collections import defaultdict
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_joint_fourpair_resultant_20261012'
GEOMETRY = ROOT / 'n41_w7_entropy_cubic_20261011/w8/geometry.json'
UNIVERSAL = ROOT / 'n131_w15_rotated_fouratom_inverse_20261010/resultant.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_INDEXED_TWO_BLOCK_N41_SOURCE_AND_TARGETS'
    assert protocol['source_sha256']['runner'] == sha(Path(__file__))
    assert protocol['source_sha256']['universal'] == sha(UNIVERSAL)
    assert protocol['source_sha256']['geometry'] == sha(GEOMETRY)
    base = PolynomialRing(GF(2), 't')
    t = base.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    ring = PolynomialRing(field, 'z')
    universal = json.loads(UNIVERSAL.read_text())
    geometry = json.loads(GEOMETRY.read_text())
    columns = {int(row['mask']): int(row['column']) for row in geometry['rows']}
    def dec(value):
        return field(base([(int(value) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def parameters(masks, rotation):
        a, b = (dec(mask << 1) for mask in masks)
        return ((a+b)**(1 << rotation), (a*b)**(1 << rotation))
    def block(first, second):
        a, p = first
        b, q = second
        aa, bb = [a**i for i in range(9)], [b**i for i in range(9)]
        pp, qq = [p**i for i in range(9)], [q**i for i in range(9)]
        coeff = [field.zero() for _ in range(9)]
        for ea, eb, ep, eq, ez in universal['terms']:
            coeff[ez] += aa[ea]*bb[eb]*pp[ep]*qq[eq]
        return ring(coeff)
    setup_start = time.monotonic_ns()
    table = []
    for side, (j, k) in enumerate(((0, 1), (2, 3))):
        entries = []
        for option_j, option_k in itertools.product(range(9), repeat=2):
            masks_j = protocol['options'][j][option_j]
            masks_k = protocol['options'][k][option_k]
            cols = [columns[mask] for mask in (*masks_j, *masks_k)]
            if len(set(cols)) != 4:
                continue
            poly = block(parameters(masks_j, protocol['rotations'][j]),
                         parameters(masks_k, protocol['rotations'][k]))
            roots = poly.roots()
            assert poly.degree() == 8 and sum(n for _, n in roots) == 8
            assert all(n == 1 for _, n in roots)
            for root, _ in roots:
                entries.append({'root': enc(root), 'options': [option_j, option_k],
                                'columns': cols})
        table.append(entries)
        print('SIDE', side, len(entries), flush=True)
    index = defaultdict(list)
    for entry in table[1]:
        index[entry['root']].append(entry)
    setup_ns = time.monotonic_ns()-setup_start
    save('root_table.json', {'status': 'PASS_REUSABLE_TWO_BLOCK_ROOT_TABLE',
                            'candidate_id': None, 'sides': table,
                            'protocol_sha256': sha(HERE / 'protocol.json')})
    results = []
    for target in protocol['targets']:
        started = time.monotonic_ns()
        target_field = dec(target['reciprocal'])
        hits = []
        quadratic_solutions = 0
        index_probes = 0
        for left in table[0]:
            u = dec(left['root'])
            A = field.one()+(u*target_field)**2
            B = u*target_field
            C = u**2+target_field**2
            polynomial = ring([C, B, A])
            solutions = ([(dec(value), 1) for value in index]
                         if polynomial == 0 else polynomial.roots())
            quadratic_solutions += len(solutions)
            for v, multiplicity in solutions:
                assert multiplicity in (1, 2)
                index_probes += 1
                for right in index.get(enc(v), ()):
                    if len(set(left['columns']+right['columns'])) != 8:
                        continue
                    assert (1+(u*v)**2)*target_field**2 + u*v*target_field + (u+v)**2 == 0
                    hits.append({'left_options': left['options'],
                                 'right_options': right['options'],
                                 'left_root': left['root'], 'right_root': right['root']})
        elapsed = time.monotonic_ns()-started
        results.append({'label': target['label'], 'target_reciprocal': target['reciprocal'],
                        'target_query_ns': elapsed, 'left_roots': len(table[0]),
                        'right_roots': len(table[1]),
                        'quadratic_solutions': quadratic_solutions,
                        'index_probes': index_probes, 'hits': hits})
        print('TARGET', target['label'], 'probes', index_probes, 'hits', len(hits), flush=True)
    record = {'status': 'PASS_INDEXED_TWO_BLOCK_QUERIES', 'candidate_id': None,
              'root_table_sha256': sha(HERE / 'root_table.json'),
              'setup_ns': setup_ns, 'queries': results,
              'total_query_ns': sum(row['target_query_ns'] for row in results),
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json')}
    save('result.json', record)
    assert (setup_ns+record['total_query_ns'])/1e9 < protocol['wall_cap_seconds']
    assert record['peak_self_rss_raw'] < protocol['rss_observational_boundary_bytes']
    print(record['status'], flush=True)


if __name__ == '__main__':
    main()
