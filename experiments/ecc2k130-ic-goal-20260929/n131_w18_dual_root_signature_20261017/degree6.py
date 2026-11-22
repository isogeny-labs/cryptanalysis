"""Frozen degree-six extension of the dual-signature ANF intersection."""
import hashlib
import itertools
import json
import signal
import sys
import time
from pathlib import Path

import census

BASE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(name, obj):
    with (BASE / name).open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def insert(basis, value):
    while value:
        pivot = value.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = value
            return
        value ^= basis[pivot]


def main(mode):
    sources = {'script': digest(Path(__file__)),
               'table': digest(census.TABLE),
               'census_result': digest(BASE / 'result.json'),
               'intersection_result': digest(BASE / 'intersection_result.json'),
               'independent_audit': digest(BASE / 'audit_result.json')}
    if mode == 'freeze':
        put('degree6_protocol.json', {'status': 'FROZEN_DEGREE6_EXTENSION',
             'source_sha256': sources, 'degree': 6, 'worker_count': 1,
             'wall_cap_seconds': 180})
        return
    assert mode == 'run'
    start = time.monotonic_ns()
    signal.alarm(180)
    protocol = json.loads((BASE / 'degree6_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_DEGREE6_EXTENSION'
    assert protocol['source_sha256'] == sources
    table = census.read_rows()
    masks = json.loads((BASE / 'result.json').read_text())['dual_masks']
    variables = [0] * 17
    labels = [0] * len(masks)
    for index, (code, root, _) in enumerate(table):
        bit = 1 << index
        for j in range(17):
            if code >> j & 1:
                variables[j] |= bit
        for j, mask in enumerate(masks):
            if (root & mask).bit_count() & 1:
                labels[j] |= bit
    label_basis = {}
    for label in labels:
        insert(label_basis, label)
    assert len(label_basis) == 113
    features = {}
    count = 0
    full = (1 << len(table)) - 1
    for degree in range(7):
        for monom in itertools.combinations(range(17), degree):
            value = full
            for j in monom:
                value &= variables[j]
            insert(features, value)
            count += 1
    quotient = {}
    pivots = sorted(features, reverse=True)
    for label in labels:
        value = label
        for pivot in pivots:
            if value >> pivot & 1:
                value ^= features[pivot]
        insert(quotient, value)
    result = {'status': 'PASS_DEGREE6_EXTENSION',
              'source_rows': len(table), 'feature_count': count,
              'feature_rank': len(features), 'signature_rank': len(label_basis),
              'quotient_signature_rank': len(quotient),
              'intersection_dimension': len(label_basis) - len(quotient),
              'elapsed_ns': time.monotonic_ns() - start,
              'protocol_sha256': digest(BASE / 'degree6_protocol.json')}
    put('degree6_result.json', result)
    signal.alarm(0)
    print(result['status'], result['feature_rank'], result['intersection_dimension'])


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
