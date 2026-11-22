"""Independent GF(2^41) replay of saved rectangle certificates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
MASK = (1 << 41) - 1
REDUCE = (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def powers(value, degree):
    result = [1]
    for _ in range(degree):
        result.append(mul(result[-1], value))
    return result


def product(geometry, slot, source_mask):
    out = 0
    for i, basis in enumerate(geometry['blocks'][slot]['product_basis']):
        if source_mask >> i & 1:
            out ^= basis
    return out


def rectangle_values(geometry, tensor, bits, prefixes):
    size = 1 << bits
    values = [0] * size**3
    for lp in range(size):
        first = product(geometry, 0, (prefixes[0] << bits) | lp)
        pp = powers(first, 16)
        specialized = [(qi, ri, reduce_xor(mul(pp[pi], c) for pi, c in coeff))
                       for qi, ri, coeff in tensor]
        for lq in range(size):
            second = product(geometry, 1, (prefixes[1] << bits) | lq)
            qq = powers(second, 16)
            cp = [0] * 25
            for qi, ri, c in specialized:
                cp[ri] ^= mul(qq[qi], c)
            for lr in range(size):
                third = product(geometry, 2, (prefixes[2] << bits) | lr)
                value = 0
                for c in reversed(cp):
                    value = mul(value, third) ^ c
                values[lp | (lq << bits) | (lr << (2*bits))] = value
    return values


def reduce_xor(values):
    result = 0
    for value in values:
        result ^= value
    return result


def affine_rank(values, bits):
    coefficients = values[:]
    for bit in range(bits):
        for mask in range(1 << bits):
            if mask >> bit & 1:
                coefficients[mask] ^= coefficients[mask ^ (1 << bit)]
    basis = {}
    for value in coefficients[1:]:
        for pivot in sorted(basis, reverse=True):
            if value >> pivot & 1:
                value ^= basis[pivot]
        if value:
            basis[value.bit_length() - 1] = value
    return len(basis)


def main():
    protocol_path = HERE / 'protocol.json'
    result_path = HERE / 'result.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    paths = {'rectangle.py': HERE / 'rectangle.py', 'geometry.json': GEOMETRY,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    assert result['status'] == 'PASS_N41_TRACE_RECTANGLE_RANK_SURVEY'
    assert result['protocol_sha256'] == sha(protocol_path)
    assert result['source_sha256'] == protocol['source_sha256']
    assert protocol['source_sha256'] == {key: sha(path) for key, path in paths.items()}
    assert result['peak_self_rss_raw'] < protocol['resource_envelope']['rss_boundary_bytes']
    geometry = json.loads(GEOMETRY.read_text())
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    records = []
    rank_probes = []
    for panel in result['panels']:
        label = panel['label']
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())['coefficient_terms']
        zero_count = len(next(x for x in sweep['panels'] if x['name'] == label)['zero_triples'])
        for width in panel['widths']:
            bits = width['low_bits_per_slot']
            assert width['valid_triples'] == 64000
            assert width['valid_zero_rectangles'] == zero_count
            assert sum(width['full_rank_histogram'].values()) == width['rectangles']
            assert sum(width['valid_rank_histogram'].values()) == width['rectangles']
            assert width['full_certified_rectangles'] <= width['valid_certified_rectangles']
            assert width['full_certified_valid_triples'] <= width['valid_certified_valid_triples']
            for example in width['certificate_examples']:
                values = rectangle_values(geometry, tensor, bits, example['prefixes'])
                functional = example['functional_mask']
                assert all((functional & value).bit_count() & 1 for value in values)
                assert affine_rank(values, 3*bits) == example['rank']
                assert values[0] == example['first_value']
                records.append({'label': label, 'bits': bits,
                                'prefixes': example['prefixes'], 'values_checked': len(values),
                                'rank': example['rank'], 'functional_mask': functional})
            if bits >= 2:
                first_prefix = min(mask >> bits for mask in geometry['permitted_canonical_a'])
                prefixes = [first_prefix] * 3
                values = rectangle_values(geometry, tensor, bits, prefixes)
                rank = affine_rank(values, 3*bits)
                assert rank == 41
                assert width['full_rank_histogram'] == {'41': width['rectangles']}
                rank_probes.append({'label': label, 'bits': bits,
                                    'prefixes': prefixes, 'values_checked': len(values),
                                    'rank': rank})
        witness = protocol['witness_masks']
        witness_products = [product(geometry, i, mask) for i, mask in enumerate(witness)]
        pp, qq, rr = (powers(witness_products[0], 16),
                      powers(witness_products[1], 16),
                      powers(witness_products[2], 24))
        value = 0
        for qi, ri, coeff in tensor:
            coefficient = reduce_xor(mul(pp[pi], c) for pi, c in coeff)
            value ^= mul(mul(qq[qi], rr[ri]), coefficient)
        if label == 'witness':
            assert value == 0
        else:
            assert value != 0
    receipt = {'status': 'PASS_INDEPENDENT_TRACE_RECTANGLE_CERTIFICATES',
               'records': records, 'rank_probes': rank_probes,
               'result_sha256': sha(result_path),
               'verifier_sha256': sha(Path(__file__))}
    (HERE / 'verification.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(receipt['status'], len(records), len(rank_probes), flush=True)


if __name__ == '__main__':
    main()
