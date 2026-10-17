#!/usr/bin/env python3
"""Exact GF(2) degree screen for code-dependent N41 RR sign duals."""
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_rr_pairwise_certificate_20261017/result.json'
WIDTH = 41


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, sort_keys=True, indent=2)
        file.write('\n')


def monomials(degree):
    return [sum(1 << bit for bit in bits)
            for d in range(degree + 1)
            for bits in itertools.combinations(range(8), d)]


def row(code, coefficient, monoms):
    out = 0
    for i, mask in enumerate(monoms):
        if code & mask == mask:
            out |= coefficient << (WIDTH * i)
    return out


def equations(charts, monoms):
    for chart_index, chart in enumerate(charts):
        for coefficient_index, coefficient in enumerate(chart['coefficients']):
            if coefficient:
                yield (row(chart['mask'], coefficient, monoms),
                       int(coefficient_index == 0),
                       [chart_index, coefficient_index])


def solve(charts, monoms):
    basis = {}
    labels = []
    start = time.monotonic_ns()
    for vector, right, label in equations(charts, monoms):
        witness = 1 << len(labels)
        labels.append(label)
        while vector:
            pivot = vector.bit_length() - 1
            if pivot in basis:
                prior, prior_right, prior_witness = basis[pivot]
                vector ^= prior
                right ^= prior_right
                witness ^= prior_witness
            else:
                basis[pivot] = (vector, right, witness)
                break
        if not vector and right:
            return {'status': 'INCONSISTENT', 'rank_at_conflict': len(basis),
                    'equations_until_conflict': len(labels),
                    'conflict_labels': [labels[i] for i in range(len(labels))
                                        if witness >> i & 1],
                    'elapsed_ns': time.monotonic_ns() - start}
    solution = 0
    for pivot in sorted(basis):
        vector, right, _ = basis[pivot]
        bit = right ^ ((vector & solution).bit_count() & 1)
        solution |= bit << pivot
    blocks = [(solution >> (WIDTH*i)) & ((1 << WIDTH)-1)
              for i in range(len(monoms))]
    for vector, right, _ in equations(charts, monoms):
        assert (vector & solution).bit_count() & 1 == right
    return {'status': 'SAT', 'rank': len(basis),
            'equations': len(labels), 'solution_blocks': blocks,
            'elapsed_ns': time.monotonic_ns() - start}


def freeze():
    source = json.loads(SOURCE.read_text())
    assert source['status'] == 'COMPLETE_N41_RR_PAIRWISE_CENSUS'
    assert source['chart_count'] == 35 and source['single_certifiable'] == 35
    save('protocol.json', {'status': 'FROZEN_CODE_PARAMETRIC_SIGN_DUAL',
         'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
         'source_sha256': sha(SOURCE), 'script_sha256': sha(Path(__file__)),
         'degrees': [0, 1, 2, 3], 'code_bits': 8, 'field_bits': WIDTH,
         'equation_law': 'constant dot=1; each nonconstant sign coefficient dot=0',
         'candidate_id': None})


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['source_sha256'] == sha(SOURCE)
    assert protocol['script_sha256'] == sha(Path(__file__))
    source = json.loads(SOURCE.read_text())
    charts = source['charts']
    assert len(charts) == 35 and len({c['mask'] for c in charts}) == 35
    results = []
    for degree in protocol['degrees']:
        monoms = monomials(degree)
        answer = solve(charts, monoms)
        answer.update({'degree': degree, 'monomials': monoms,
                       'unknown_bits': WIDTH * len(monoms)})
        results.append(answer)
        print(degree, answer['status'], answer.get('rank', answer.get('rank_at_conflict')),
              answer['elapsed_ns'], flush=True)
    save('result.json', {'status': 'PASS_CODE_PARAMETRIC_SIGN_DUAL_SCREEN',
         'candidate_id': None, 'protocol_sha256': sha(HERE / 'protocol.json'),
         'source_sha256': sha(SOURCE), 'charts': len(charts), 'results': results})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
