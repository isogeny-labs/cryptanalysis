"""Freeze exact source options and two N41 target reciprocals."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_joint_fourpair_resultant_20261012'
FIXTURE = ROOT / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json'
PAIRS = ROOT / 'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv'
GEOMETRY = ROOT / 'n41_w7_entropy_cubic_20261011/w8/geometry.json'
UNIVERSAL = ROOT / 'n131_w15_rotated_fouratom_inverse_20261010/resultant.json'
NEGATIVE = ROOT / 'n41_cofactor4_public_equation_20261016/circuit_protocol.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    panel = json.loads((PRIOR / 'panel.json').read_text())
    fixture = json.loads(FIXTURE.read_text())
    negative = json.loads(NEGATIVE.read_text())
    assert panel['sha256']['fixture'] == sha(FIXTURE)
    assert panel['sha256']['pairs'] == sha(PAIRS)
    assert panel['sha256']['geometry'] == sha(GEOMETRY)
    assert panel['sha256']['universal_resultant'] == sha(UNIVERSAL)
    positive = panel['families'][0]['masks']
    options = [[positive[j]] for j in range(4)]
    for j in range(4):
        for k in range(8):
            label = f'slot{j}_alternative{k}'
            row = next(row for row in panel['families'] if row['id'] == label)
            options[j].append(row['masks'][j])
    assert all(len(slot) == 9 for slot in options)
    allowed = [set() for _ in range(4)]
    with PAIRS.open() as file:
        assert file.readline().strip() == 'ECC2K41_ALLSEED4 4 4'
        for line in file:
            fields = line.split()
            if fields[0] == 'S':
                slot, _, a, b = map(int, fields[1:5])
                allowed[slot].add((a, b))
    for j in range(4):
        assert all(tuple(pair) in allowed[j] for pair in options[j])
    base = PolynomialRing(GF(2), 't')
    t = base.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    def decode(value):
        return field(base([(int(value) >> i) & 1 for i in range(41)]))
    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    assert negative['public_point'] != panel['public_target']
    negative_reciprocal = encode(~decode(negative['raw_target'][0]))
    record = {'status': 'FROZEN_INDEXED_TWO_BLOCK_N41_SOURCE_AND_TARGETS',
              'candidate_id': None, 'curve_id': panel['curve_id'],
              'options': options, 'rotations': panel['rotations'],
              'targets': [
                  {'label': 'positive_control', 'raw_point': fixture['raw_target'],
                   'public_point': panel['public_target'],
                   'reciprocal': panel['target_reciprocal']},
                  {'label': 'independent_public_control',
                   'raw_point': negative['raw_target'],
                   'public_point': negative['public_point'],
                   'reciprocal': negative_reciprocal}],
              'one_worker': True, 'wall_cap_seconds': 180,
              'rss_observational_boundary_bytes': 4*1024**3,
              'source_sha256': {'runner': sha(HERE / 'run_sage.py'),
                  'panel': sha(PRIOR / 'panel.json'), 'fixture': sha(FIXTURE),
                  'pairs': sha(PAIRS), 'geometry': sha(GEOMETRY),
                  'universal': sha(UNIVERSAL), 'negative_target': sha(NEGATIVE),
                  'sage_runtime': sha(HERE / 'sage_runtime_info.json')}}
    assert record['targets'][0]['reciprocal'] == encode(~decode(fixture['raw_target'][0]))
    with (HERE / 'protocol.json').open('x') as file:
        json.dump(record, file, indent=2, sort_keys=True)
        file.write('\n')
    print(record['status'], [len(slot) for slot in options])


if __name__ == '__main__':
    main()
