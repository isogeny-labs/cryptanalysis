#!/usr/bin/env python3
"""Derive an adjacent-rotation N41 source from the frozen linked panel."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_n131_linked_frobenius_pair_20261012'
SOURCE = ROOT / 'n41_w8_sixpair_mitm_20261011/join_input.tsv'
MODULUS = (1 << 41) | (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def square(value):
    result = 0
    while value:
        low = value & -value
        result ^= 1 << (2 * (low.bit_length()-1))
        value ^= low
    for bit in range(result.bit_length()-1, 40, -1):
        if result >> bit & 1:
            result ^= MODULUS << (bit-41)
    return result


def prepare():
    source = SOURCE.read_text().splitlines()
    slot_zero = {}
    for line in source:
        words = line.split()
        if words and words[0] == 'S' and words[1] == '0':
            slot_zero[int(words[2])] = (int(words[-2]), int(words[-1]))
    assert len(slot_zero) == 140
    output = []
    changed = 0
    for line in source:
        words = line.split()
        if words and words[0] == 'S' and words[1] == '1':
            sid = int(words[2])
            x, y = slot_zero[sid]
            words[-2:] = [str(square(x)), str(square(y))]
            line = ' '.join(words)
            changed += 1
        output.append(line)
    assert changed == 140
    (HERE / 'adjacent_input.tsv').write_text('\n'.join(output)+'\n')
    native = (PRIOR / 'join_linked.cpp').read_text()
    assert native.count('step < 7') == 1
    (HERE / 'adjacent_join.cpp').write_text(native.replace('step < 7', 'step < 1'))
    audit = (PRIOR / 'audit_sage.py').read_text()
    replacements = {
        'INPUT = ROOT / "n41_w8_sixpair_mitm_20261011/join_input.tsv"':
            'INPUT = HERE / "adjacent_input.tsv"',
        'ROTATIONS = (0, 7, 14, 21, 28, 35)':
            'ROTATIONS = (0, 1, 14, 21, 28, 35)',
        ')), 7))': ')), 1))',
        'pow(eigenvalue, 7, R)': 'pow(eigenvalue, 1, R)',
        '"linked_frobenius_exponent": 7': '"linked_frobenius_exponent": 1',
    }
    for before, after in replacements.items():
        assert audit.count(before) == 1, before
        audit = audit.replace(before, after)
    marker = 'hit_lines = [line.split() for line in (HERE / "stdout.log").read_text().splitlines()'
    assert audit.count(marker) == 1
    identity = '''# Exact adjacent-Frobenius map on every frozen signed source state.
for sid in range(140):
    point = curve(*map(dec, input_states[(0, sid)]))
    x = point[0]
    assert x not in (0, 1)
    near = frobenius(point, 1)
    plus = point + near
    minus = point - near
    f = x + 1/x
    assert plus != curve(0) and minus != curve(0)
    assert plus[0] == f and minus[0] == f + 1/f

'''
    audit = audit.replace(marker, identity+marker)
    (HERE / 'audit_sage.py').write_text(audit)
    receipt = {'status': 'FROZEN_ADJACENT_SOURCE_DERIVATION',
               'transformed_states': changed,
               'source_sha256': {'original_input': sha(SOURCE),
                                 'original_native': sha(PRIOR / 'join_linked.cpp'),
                                 'original_sage_audit': sha(PRIOR / 'audit_sage.py'),
                                 'preparer': sha(Path(__file__))},
               'output_sha256': {name: sha(HERE / name)
                                 for name in ('adjacent_input.tsv', 'adjacent_join.cpp', 'audit_sage.py')}}
    with (HERE / 'prepare_result.json').open('x') as file:
        json.dump(receipt, file, sort_keys=True, indent=2)
        file.write('\n')
    print(receipt['status'])


if __name__ == '__main__':
    prepare()
