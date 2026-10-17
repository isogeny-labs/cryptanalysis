"""Independent GF(2^41) evaluation of every frozen prefix product."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
MASK = (1 << 41) - 1
REDUCE = (1 << 3) | 1


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> 41:
            a = (a & MASK) ^ REDUCE
    return out


def powers(x, last):
    result = [1]
    for _ in range(last):
        result.append(mul(result[-1], x))
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = []
    for version, protocol_name, result_name in (
            ('v1', 'protocol.json', 'result.json'),
            ('v2', 'protocol_v2.json', 'result_v2.json')):
        protocol_path = HERE / protocol_name
        result_path = HERE / result_name
        protocol = json.loads(protocol_path.read_text())
        result = json.loads(result_path.read_text())
        assert result['status'] == 'PASS_N41_UNIVERSAL_NORM_DENSITY'
        assert result['protocol_sha256'] == sha(protocol_path)
        assert result['source_sha256'] == protocol['source_sha256']
        for label in ('witness', 'negative'):
            source_path = SOURCE / (label + '_result_v2.json')
            assert sha(source_path) == protocol['source_sha256'][source_path.name]
            tensor = json.loads(source_path.read_text())['coefficient_terms']
            p = powers(protocol['witness_first_product'], 16)
            r = powers(protocol['witness_third_product'], 24)
            cp = {}
            for qi, ri, coeff in tensor:
                value = 0
                for pi, c in coeff:
                    value ^= mul(p[pi], c)
                cp[qi, ri] = value
            prefix_product = 1
            expected = {x['q_count']: x for x in next(
                panel for panel in result['panels'] if panel['label'] == label)['checkpoints']}
            for count, qvalue in enumerate(protocol['q_order'], 1):
                q = powers(qvalue, 16)
                factor = 0
                for (qi, ri), c in cp.items():
                    factor ^= mul(mul(q[qi], r[ri]), c)
                prefix_product = mul(prefix_product, factor)
                if count in expected:
                    assert prefix_product == expected[count]['witness_evaluation']
                    assert expected[count]['direct_evaluation_matches']
                    records.append({'version': version, 'panel': label, 'q_count': count,
                                    'independent_product': prefix_product})
            if label == 'witness':
                assert all(x['independent_product'] == 0 for x in records
                           if x['version'] == version and x['panel'] == label)
            else:
                assert all(x['independent_product'] != 0 for x in records
                           if x['version'] == version and x['panel'] == label)
    verification = {'status': 'PASS_INDEPENDENT_GF2_41_PREFIX_PRODUCTS',
                    'field_modulus': 't^41+t^3+1', 'records': records,
                    'source_sha256': {path.name: sha(path) for path in (
                        HERE / 'verify.py', HERE / 'protocol.json', HERE / 'protocol_v2.json',
                        HERE / 'result.json', HERE / 'result_v2.json')}}
    (HERE / 'verification.json').write_text(json.dumps(verification, indent=2, sort_keys=True) + '\n')
    print(verification['status'], len(records))


if __name__ == '__main__':
    main()
