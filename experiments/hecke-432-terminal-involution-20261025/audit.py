"""Replay terminal-edge pairing on the complete p=997 rational and geometric data."""
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P = 997


def read(relative):
    path = ROOT/relative
    return json.loads(path.read_text()), sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    census, census_hash = read('hecke-432-prime997-20261025/census.json')
    image, image_hash = read('hecke-432-prime997-20261025/image.json')
    geometric, geometric_hash = read('hecke-432-geometric-fiber-20261025/evaluation.json')
    prior, prior_hash = read('hecke-432-geometric-fiber-20261025/audit.json')
    assert protocol['status'] == 'FROZEN_BEFORE_TERMINAL_INVOLUTION_AUDIT'
    assert census['prime'] == image['prime'] == P
    assert prior['status'] == 'PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT'
    assert census['paired_chain_count'] == image['row_count'] == len(image['rows']) == 1800
    sources = {(tuple(row['curve_ainvs']),row['label']):row for row in census['rows']}
    assert len(sources) == len(census['rows'])
    rational = defaultdict(list)
    for row in image['rows']:
        source_key = (tuple(row['source_ainvs']),row['source_label'])
        source = sources[source_key]
        two_index, three_index = row['pair']
        assert 0 <= three_index < len(source['three_paths'])
        edges = source['two_paths'][two_index]
        assert len(edges) == 4
        prefix = tuple(edge['kernel_x'] for edge in edges[:3])
        last = edges[-1]['kernel_x']
        assert len(row['projections']) == 1
        point = row['projections'][0]['E_point']
        assert point is not None and len(point) == 2
        rational[source_key,three_index,prefix].append((last,point))
    assert len(rational) == 900
    rational_failures = []
    for key, members in rational.items():
        if len(members) != 2:
            rational_failures.append((key,'wrong_size'))
            continue
        (last0,p0),(last1,p1) = members
        if last0 == last1 or p0[0] != p1[0] or (p0[1]+p1[1]) % P:
            rational_failures.append((key,'projection_mismatch'))
    assert not rational_failures,rational_failures[:3]
    assert geometric['status'] == 'COMPLETE_GEOMETRIC_E_FIBER'
    assert len(geometric['rows']) == 24
    groups = defaultdict(list)
    for row in geometric['rows']:
        assert row['status'] == 'PASS' and row['E_point'] is not None
        vectors = row['root_vectors']
        assert len(vectors) == 4
        groups[tuple(tuple(v) for v in vectors[:3])].append(row)
    assert len(groups) == 12
    geometric_failures = []
    pairs = []
    for prefix,members in groups.items():
        if len(members) != 2:
            geometric_failures.append((prefix,'wrong_size'))
            continue
        a,b = members
        xa,ya = a['E_point']
        xb,yb = b['E_point']
        if (a['root_vectors'][-1] == b['root_vectors'][-1] or xa != xb
                or any((u+v)%P for u,v in zip(ya,yb))):
            geometric_failures.append((prefix,'projection_mismatch'))
        pairs.append([a['index'],b['index']])
    assert not geometric_failures,geometric_failures[:3]
    assert len({tuple(row['E_point'][1]) for row in geometric['rows']}) == 24
    assert len({tuple(row['E_point'][0]) for row in geometric['rows']}) == 12
    out = {
        'status':'PASS_TERMINAL_EDGE_NEGATION_AUDIT',
        'prime':P,'rational_source_records':1800,'rational_terminal_pairs':900,
        'rational_pair_failures':len(rational_failures),
        'geometric_source_records':24,'geometric_terminal_pairs':12,
        'geometric_pair_failures':len(geometric_failures),
        'geometric_pair_indices':sorted(pairs),
        'source_sha256':{'census':census_hash,'image':image_hash,
                         'geometric_evaluation':geometric_hash,
                         'geometric_independent_audit':prior_hash},
        'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
    }
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','rational_source_records',
                       'rational_terminal_pairs','geometric_source_records',
                       'geometric_terminal_pairs')},sort_keys=True))


if __name__ == '__main__':
    main()
