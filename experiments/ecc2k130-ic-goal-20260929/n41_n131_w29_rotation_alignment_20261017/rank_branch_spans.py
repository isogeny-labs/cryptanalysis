"""Exact GF(2) ranks of five pair-root difference spaces by rotation."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {'n41': ROOT / 'n41_w9_lazy_source_20261017/circuit.py',
           'n131': ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'}
ROTATIONS = {'n41': {'original': [0, 6, 12, 18, 24],
                      'aligned': [0, 0, 12, 12, 24]},
             'n131': {'original': [0, 18, 36, 54, 72],
                       'aligned': [0, 0, 36, 36, 72]}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(vectors):
    pivots = {}
    for value in vectors:
        v = value
        while v:
            bit = v.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = v
                break
            v ^= pivots[bit]
    return len(pivots)


protocol = {'status': 'FROZEN_BEFORE_BRANCH_SPAN_RANK',
            'rotation_schedules': ROTATIONS,
            'source_sha256': {'script': sha(Path(__file__)),
                              **{name: sha(path) for name, path in SOURCES.items()}}}
with (HERE / 'branch_rank_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')

rows = {}
for name, source in SOURCES.items():
    spec = importlib.util.spec_from_file_location(f'branch_span_{name}', source)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    assert design.ROTATIONS == ROTATIONS[name]['original']
    diff = [design.F.mul(value, design.F.inverse(design.C)) for value in design.PB]
    assert rank(diff) == len(diff)
    cases = {}
    for variant, rotations in ROTATIONS[name].items():
        slot_bases = [[design.F.frob(value, rotation) for value in diff]
                      for rotation in rotations]
        prefix_ranks = [rank([value for base in slot_bases[:i] for value in base])
                        for i in range(1, 6)]
        cases[variant] = {'rotations': rotations,
                          'slot_basis_rank': len(diff),
                          'prefix_ranks': prefix_ranks,
                          'annihilator_dimension': design.N - prefix_ranks[-1]}
    rows[name] = {'field_degree': design.N,
                  'source_product_rank': len(diff), 'cases': cases}

result = {'status': 'PASS_EXACT_BRANCH_DIFFERENCE_RANKS', 'rows': rows,
          'protocol_sha256': sha(HERE / 'branch_rank_protocol.json')}
with (HERE / 'branch_rank_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True))
