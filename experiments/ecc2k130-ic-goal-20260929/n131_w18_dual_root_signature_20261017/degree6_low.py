"""Independent low-pivot check of the degree-six screen."""
import hashlib
import itertools
import json
import signal
import sys
import time
from pathlib import Path

import audit

BASE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(name, obj):
    with (BASE / name).open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def main(mode):
    sources = {'script': digest(Path(__file__)),
               'audit_script': digest(BASE / 'audit.py'),
               'table': digest(audit.TABLE),
               'degree6_result': digest(BASE / 'degree6_result.json')}
    if mode == 'freeze':
        put('degree6_low_protocol.json', {'status': 'FROZEN_DEGREE6_LOW_PIVOT_CHECK',
            'source_sha256': sources, 'worker_count': 1, 'wall_cap_seconds': 180})
        return
    assert mode == 'run'
    signal.alarm(180)
    start = time.monotonic_ns()
    protocol = json.loads((BASE / 'degree6_low_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_DEGREE6_LOW_PIVOT_CHECK'
    assert protocol['source_sha256'] == sources
    table = audit.rows()
    delta = {}
    for _, x, y in table:
        audit.insert(delta, x ^ y)
    assert len(delta) == 17
    for pivot in sorted(delta, reverse=True):
        for other in delta:
            if other != pivot and delta[other] >> pivot & 1:
                delta[other] ^= delta[pivot]
    masks = [1 << j | sum(1 << p for p, row in delta.items() if row >> j & 1)
             for j in range(131) if j not in delta]
    assert len(masks) == 114
    variables = [0] * 17
    labels = [0] * 114
    for index, (code, x, y) in enumerate(table):
        bit = 1 << index
        for j in range(17):
            if code >> j & 1:
                variables[j] |= bit
        for j, mask in enumerate(masks):
            assert ((x ^ y) & mask).bit_count() % 2 == 0
            if (x & mask).bit_count() & 1:
                labels[j] |= bit
    label_basis = {}
    for label in labels:
        audit.insert(label_basis, label)
    assert len(label_basis) == 113
    features = {}
    count = 0
    full = (1 << len(table)) - 1
    for degree in range(7):
        for monom in itertools.combinations(range(17), degree):
            value = full
            for j in monom:
                value &= variables[j]
            audit.insert(features, value)
            count += 1
    quotient = {}
    for label in labels:
        value = label
        for pivot in sorted(features):
            if value >> pivot & 1:
                value ^= features[pivot]
        audit.insert(quotient, value)
    result = {'status': 'PASS_INDEPENDENT_DEGREE6_LOW_PIVOT',
              'source_rows': len(table), 'feature_count': count,
              'feature_rank': len(features), 'signature_rank': len(label_basis),
              'quotient_signature_rank': len(quotient),
              'intersection_dimension': len(label_basis) - len(quotient),
              'elapsed_ns': time.monotonic_ns() - start,
              'protocol_sha256': digest(BASE / 'degree6_low_protocol.json')}
    prior = json.loads((BASE / 'degree6_result.json').read_text())
    for key in ('source_rows', 'feature_count', 'feature_rank', 'signature_rank',
                'quotient_signature_rank', 'intersection_dimension'):
        assert result[key] == prior[key]
    put('degree6_low_result.json', result)
    signal.alarm(0)
    print(result['status'], result['intersection_dimension'])


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
