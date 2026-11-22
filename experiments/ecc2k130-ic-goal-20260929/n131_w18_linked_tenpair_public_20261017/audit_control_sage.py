#!/usr/bin/env sage -python
"""Independent Sage reconstruction of the linked ten-pair control."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / 'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'
ARCHIVE = ROOT / 'n131_w18_tenpair_binary_frob_20261012/control_fixture.json'
RUNTIME = HERE / 'sage_runtime_info.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths():
    return {'script': Path(__file__), 'fixture': HERE / 'control_fixture.json',
            'support': SUPPORT, 'archived_fixture': ARCHIVE, 'runtime': RUNTIME}


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def freeze():
    save('control_sage_protocol.json', {'status': 'FROZEN_LINKED_CONTROL_SAGE_AUDIT',
         'source_sha256': {name: sha(path) for name, path in paths().items()}})


def run():
    from sage.all import EllipticCurve, GF, PolynomialRing
    protocol = json.loads((HERE / 'control_sage_protocol.json').read_text())
    assert protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    fixture = json.loads((HERE / 'control_fixture.json').read_text())
    assert fixture['status'] == 'CONSTRUCTED_LINKED_TENPAIR_FIXTURE'
    assert fixture['archived_fixture_sha256'] == sha(ARCHIVE)
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    ring = PolynomialRing(GF(2), 't')
    t = ring.gen()
    field = GF(2**131, name='t', modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(131)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def halftrace(value):
        result, power = field.zero(), value
        for _ in range(66):
            result += power
            power = power**4
        assert result**2 + result == value
        return result
    def coordinates(point):
        return [enc(point[0]), enc(point[1])]
    matched = []
    all_columns = []
    for slot, item in enumerate(fixture['selected']):
        assert item['slot'] == slot
        assert item['masks'][0] ^ item['masks'][1] == 212
        assert item['folded_columns'] == [columns[mask] for mask in item['masks']]
        all_columns.extend(item['folded_columns'])
        options = []
        for mask in item['masks']:
            u = halftrace(dec(mask << 1))
            options.append(curve.lift_x(1 + 1/u, all=True))
        choices = []
        for a, b in itertools.product(*options):
            point = a+b
            if point == curve(0) or point[0] in (0, 1):
                continue
            rotated = curve(point[0]**(1 << item['rotation']),
                            point[1]**(1 << item['rotation']))
            if coordinates(rotated) == fixture['points'][slot]:
                assert enc(1/(point[0]+1)) == item['unrotated_pair_output_z']
                choices.append((a,b,rotated))
        assert len(choices) == 1, (slot, len(choices))
        matched.append(choices[0])
    assert fixture['selected'][0]['masks'] == fixture['selected'][1]['masks']
    assert fixture['selected'][0]['folded_columns'] == fixture['selected'][1]['folded_columns']
    assert len(all_columns) == 20 and len(set(all_columns)) == 18
    assert len(set(all_columns[::2])) == 9
    assert coordinates(curve(matched[0][2][0]**(1 << 16),
                             matched[0][2][1]**(1 << 16))) == fixture['points'][1]
    total = sum((row[2] for row in matched), curve(0))
    assert coordinates(total) == fixture['target']
    order = 680564733841876926932320129493409985129
    assert order*(4*total) == curve(0)
    save('control_sage_audit.json', {'status': 'PASS_LINKED_TENPAIR_SAGE_CONTROL',
         'candidate_id': None, 'source_pair_slots': 10,
         'independent_source_edges': 9, 'distinct_folded_columns': 18,
         'raw_target': fixture['target'],
         'projected_target': coordinates(4*total),
         'protocol_sha256': sha(HERE / 'control_sage_protocol.json'),
         'source_sha256': protocol['source_sha256']})
    print('PASS_LINKED_TENPAIR_SAGE_CONTROL')


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
