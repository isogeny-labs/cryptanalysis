#!/usr/bin/env python3
"""Exact finite-field census for fixed and input-dependent relation coefficients."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / 'adaptive-coefficient-protocol.json'
OUTPUT = HERE / 'adaptive-coefficient-result.json'


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n').encode()


def run():
    protocol_bytes = PROTOCOL.read_bytes()
    protocol = json.loads(protocol_bytes)
    assert protocol['schema'] == 'xedni-adaptive-coefficient-protocol-v1'
    assert protocol['fixed_coefficients'] == [1, 1]
    rows = []
    for q in protocol['fields']:
        assert q in (7, 11, 31)
        fixed = adaptive = exhaustive = failure_shape = 0
        disagreements = 0
        for u in range(q):
            for v in range(q):
                fixed_hit = (u + v) % q == 0
                a, b = (v, -u) if u else (0, 1)
                adaptive_hit = b % q != 0 and (a*u+b*v) % q == 0
                witness_exists = any((aa*u+bb*v) % q == 0
                                     for bb in range(1, q) for aa in range(q))
                expected = u != 0 or v == 0
                assert witness_exists == expected
                if adaptive_hit != witness_exists:
                    disagreements += 1
                fixed += fixed_hit
                adaptive += adaptive_hit
                exhaustive += witness_exists
                failure_shape += u == 0 and v != 0
        assert disagreements == 0
        assert fixed == q and adaptive == exhaustive == q*q-q+1
        assert failure_shape == q-1
        rows.append({'q':q,'pairs':q*q,'fixed_hits':fixed,
                     'adaptive_hits':adaptive,'exhaustive_witness_hits':exhaustive,
                     'unreachable_pairs':failure_shape,'disagreements':disagreements,
                     'fixed_fraction':f'{fixed}/{q*q}',
                     'adaptive_fraction':f'{adaptive}/{q*q}'})
    result={'schema':'xedni-adaptive-coefficient-result-v1',
            'protocol_sha256':sha256(protocol_bytes).hexdigest(),
            'status':'complete','rows':rows}
    OUTPUT.write_bytes(canonical(result))
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    run()
