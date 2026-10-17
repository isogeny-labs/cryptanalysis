"""Exact Boolean-degree screen for the frozen 40-code RR row map."""
import hashlib
import itertools
import json
from pathlib import Path

import build

D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_basis(vectors):
    basis = {}
    for value in vectors:
        while value:
            high = value.bit_length() - 1
            if high in basis:
                value ^= basis[high]
            else:
                basis[high] = value
                break
    return basis


def reduced(value, basis):
    for high in sorted(basis, reverse=True):
        if (value >> high) & 1:
            value ^= basis[high]
    return value


def main():
    protocol = json.loads((D / 'protocol.json').read_text())
    assert protocol['source_sha256'] == sha(build.SOURCE)
    target, rows = build.load_source()
    assert list(target) == protocol['target']
    table = build.sign_anf(build.Field(build.N, [0, 3]), rows)
    lines = build.SOURCE.read_text().splitlines()[1:]
    masks = []
    for code in range(40):
        a = int(lines[4 * code].split()[3])
        assert all(int(lines[slot * 160 + 4 * code].split()[3]) == a
                   for slot in range(6))
        masks.append(a)
    assert len(set(masks)) == 40
    # The fixed seed 56 uses bit 5 as its highest set bit, so that bit is
    # eliminated from the canonical selector as in the archived source circuit.
    source_bits = [bit for bit in range(8) if bit != 5]
    codes = [sum(((a >> bit) & 1) << j for j, bit in enumerate(source_bits))
             for a in masks]
    assert len(set(codes)) == 40
    bases = {}
    ranks = {}
    for degree in range(4):
        monomials = [indices for size in range(degree + 1)
                     for indices in itertools.combinations(range(7), size)]
        vectors = [sum((int(all((code >> index) & 1 for index in indices)) << c)
                       for c, code in enumerate(codes)) for indices in monomials]
        bases[degree] = make_basis(vectors)
        ranks[degree] = len(bases[degree])
    assert ranks[3] == 40
    totals = {str(d): 0 for d in range(4)}
    by_term = {str(term): {str(d): 0 for d in range(4)} for term in range(4)}
    counted = 0
    for slot in range(6):
        for coordinate in range(6):
            for term in range(4):
                for bit in range(build.N):
                    word = sum((((table[slot, code][coordinate][term] >> bit) & 1) << code)
                               for code in range(40))
                    least = next(d for d in range(4) if reduced(word, bases[d]) == 0)
                    totals[str(least)] += 1
                    by_term[str(term)][str(least)] += 1
                    counted += 1
    assert counted == 6 * 6 * 4 * build.N
    result = {'status': 'EXACT_DEGREE_SCREEN', 'source_sha256': sha(build.SOURCE),
              'protocol_sha256': sha(D / 'protocol.json'),
              'source_codes': 40, 'selector_bits': source_bits,
              'field_output_bits_tested': counted,
              'monomial_span_ranks_by_degree': ranks,
              'minimum_degree_counts': totals,
              'minimum_degree_counts_by_sign_term': by_term,
              'coefficient_order': ['base', 'sign_a', 'sign_b', 'sign_a*sign_b']}
    (D / 'degree_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
