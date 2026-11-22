#!/usr/bin/env python3
"""Independent parity replay of code-dependent sign-certificate receipts."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / 'n41_rr_pairwise_certificate_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, sort_keys=True, indent=2)
        file.write('\n')


def freeze():
    files = {'script': HERE / 'audit.py', 'producer_protocol': HERE / 'protocol.json',
             'producer_result': HERE / 'result.json',
             'upstream_coefficients': UPSTREAM / 'result.json',
             'upstream_sage_audit': UPSTREAM / 'audit_result.json',
             'upstream_terminal': UPSTREAM / 'terminal.json'}
    save('audit_protocol.json', {'status': 'FROZEN_PARAMETRIC_DUAL_AUDIT',
         'source_sha256': {name: sha(path) for name, path in files.items()}})


def run():
    start = time.monotonic_ns()
    protocol = json.loads((HERE / 'audit_protocol.json').read_text())
    files = {'script': HERE / 'audit.py', 'producer_protocol': HERE / 'protocol.json',
             'producer_result': HERE / 'result.json',
             'upstream_coefficients': UPSTREAM / 'result.json',
             'upstream_sage_audit': UPSTREAM / 'audit_result.json',
             'upstream_terminal': UPSTREAM / 'terminal.json'}
    assert protocol['source_sha256'] == {name: sha(path) for name, path in files.items()}
    source = json.loads(files['upstream_coefficients'].read_text())
    producer = json.loads(files['producer_result'].read_text())
    assert producer['status'] == 'PASS_CODE_PARAMETRIC_SIGN_DUAL_SCREEN'
    charts = source['charts']
    rows = []
    for record in producer['results']:
        monoms = record['monomials']
        if record['status'] == 'INCONSISTENT':
            coordinate_parity = [0] * len(monoms)
            right_parity = 0
            for chart_index, coefficient_index in record['conflict_labels']:
                chart = charts[chart_index]
                coefficient = chart['coefficients'][coefficient_index]
                right_parity ^= int(coefficient_index == 0)
                for i, mask in enumerate(monoms):
                    if mask & chart['mask'] == mask:
                        coordinate_parity[i] ^= coefficient
            assert all(value == 0 for value in coordinate_parity)
            assert right_parity == 1
            rows.append({'degree': record['degree'], 'status': 'CONTRADICTION_REPLAYED',
                         'equations': len(record['conflict_labels'])})
        else:
            assert record['status'] == 'SAT'
            blocks = record['solution_blocks']
            assert len(blocks) == len(monoms)
            checked_coefficients = checked_signs = 0
            for chart in charts:
                mask = 0
                for monom, block in zip(monoms, blocks):
                    if monom & chart['mask'] == monom:
                        mask ^= block
                for j, coefficient in enumerate(chart['coefficients']):
                    assert (mask & coefficient).bit_count() % 2 == int(j == 0)
                    checked_coefficients += 1
                # Reconstruct every sign value from its Möbius coefficients.
                for signs in range(64):
                    value = 0
                    for monom, coefficient in enumerate(chart['coefficients']):
                        if monom & signs == monom:
                            value ^= coefficient
                    assert (mask & value).bit_count() % 2 == 1
                    checked_signs += 1
            rows.append({'degree': record['degree'], 'status': 'ALL_CHARTS_REPLAYED',
                         'coefficient_checks': checked_coefficients,
                         'sign_value_checks': checked_signs,
                         'nonzero_solution_blocks': sum(bool(block) for block in blocks)})
    assert [r['status'] for r in rows] == ['CONTRADICTION_REPLAYED']*3 + ['ALL_CHARTS_REPLAYED']
    save('audit_result.json', {'status': 'PASS_PARAMETRIC_SIGN_DUAL_REPLAY',
         'protocol_sha256': sha(HERE / 'audit_protocol.json'),
         'source_sha256': protocol['source_sha256'], 'rows': rows,
         'elapsed_ns': time.monotonic_ns() - start})
    print('PASS_PARAMETRIC_SIGN_DUAL_REPLAY')


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
