"""Independent N41 group reconstruction of every cached block root."""
import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / 'n41_w7_entropy_cubic_20261011/w8/geometry.json'
FIXTURE = ROOT / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def sources():
    return {'script': Path(__file__), 'protocol': HERE / 'protocol.json',
            'root_table': HERE / 'root_table.json', 'result': HERE / 'result.json',
            'pair_audit': HERE / 'pair_audit_result.json',
            'geometry': GEOMETRY, 'fixture': FIXTURE,
            'runtime': HERE / 'sage_runtime_info.json'}


def freeze():
    save('group_protocol.json', {'status': 'FROZEN_INDEXED_BLOCK_GROUP_AUDIT',
         'source_sha256': {name: sha(path) for name, path in sources().items()}})


def run():
    protocol = json.loads((HERE / 'group_protocol.json').read_text())
    assert protocol['source_sha256'] == {name: sha(path) for name, path in sources().items()}
    frozen = json.loads((HERE / 'protocol.json').read_text())
    table = json.loads((HERE / 'root_table.json').read_text())['sides']
    results = json.loads((HERE / 'result.json').read_text())['queries']
    geometry = json.loads(GEOMETRY.read_text())
    rows = {int(row['mask']): row for row in geometry['rows']}
    base = PolynomialRing(GF(2), 't')
    t = base.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(value):
        return field(base([(int(value) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def frob(point, exponent):
        return curve(point[0]**(1 << exponent), point[1]**(1 << exponent))
    diagonal = {}
    for mask, row in rows.items():
        raw = curve(*map(dec, row['raw_point']))
        diagonal[mask] = raw + frob(raw, 1)
    pair_cache = {}
    def pair_points(slot, option):
        key = slot, option
        if key not in pair_cache:
            a, b = (diagonal[mask] for mask in frozen['options'][slot][option])
            rotation = frozen['rotations'][slot]
            pair_cache[key] = [frob(sa*a+sb*b, rotation)
                               for sa in (1, -1) for sb in (1, -1)]
        return pair_cache[key]
    block_cache = {}
    signed_sums = 0
    for side, entries in enumerate(table):
        grouped = {}
        for entry in entries:
            grouped.setdefault(tuple(entry['options']), set()).add(entry['root'])
        j, k = ((0, 1), (2, 3))[side]
        for options, expected in grouped.items():
            points = [a+b for a in pair_points(j, options[0])
                      for b in pair_points(k, options[1])]
            assert len(points) == 16
            assert all(point != curve(0) and point[0] != 0 for point in points)
            actual = {enc(1/point[0]) for point in points}
            assert actual == expected and len(actual) == 8, (side, options)
            block_cache[side, options] = points
            signed_sums += len(points)
    assert signed_sums == 16*(600//8+616//8)
    positive = results[0]
    assert positive['label'] == 'positive_control' and len(positive['hits']) == 1
    hit = positive['hits'][0]
    left = block_cache[0, tuple(hit['left_options'])]
    right = block_cache[1, tuple(hit['right_options'])]
    target_raw = curve(*map(dec, frozen['targets'][0]['raw_point']))
    target_public = curve(*map(dec, frozen['targets'][0]['public_point']))
    assert 4*target_raw == target_public
    matched = []
    for a in left:
        if enc(1/a[0]) != hit['left_root']:
            continue
        for b in right:
            if enc(1/b[0]) != hit['right_root']:
                continue
            total = a+b
            if total != curve(0) and enc(1/total[0]) == positive['target_reciprocal']:
                assert 4*total in (target_public, -target_public)
                matched.append([enc(total[0]), enc(total[1])])
    assert matched
    save('group_result.json', {'status': 'PASS_INDEXED_BLOCK_GROUP_AUDIT',
         'candidate_id': None, 'block_families_checked': len(block_cache),
         'signed_block_sums_checked': signed_sums,
         'positive_signed_matches': len(matched),
         'positive_match_points': matched,
         'protocol_sha256': sha(HERE / 'group_protocol.json'),
         'source_sha256': protocol['source_sha256']})
    print('PASS_INDEXED_BLOCK_GROUP_AUDIT', signed_sums, len(matched))


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
