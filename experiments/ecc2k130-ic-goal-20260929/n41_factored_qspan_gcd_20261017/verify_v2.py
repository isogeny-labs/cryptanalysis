"""Independent receipt and GF(2^41) replay for the implicit q-span gate."""
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


def evaluate(tensor, first, second, third):
    pp, qq, rr = powers(first, 16), powers(second, 16), powers(third, 24)
    value = 0
    for qi, ri, pc in tensor:
        c = 0
        for pi, coefficient in pc:
            c ^= mul(pp[pi], coefficient)
        value ^= mul(mul(qq[qi], rr[ri]), c)
    return value


def main():
    protocol_path = HERE / 'protocol_v2.json'
    result_path = HERE / 'result_v2.json'
    protocol = json.loads(protocol_path.read_text())
    result = json.loads(result_path.read_text())
    files = {'factored_gcd_v2.py': HERE / 'factored_gcd_v2.py', 'geometry.json': GEOMETRY,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    assert result['status'] == 'PASS_FACTORED_QSPAN_GCD_SOURCE_GRID'
    assert result['protocol_sha256'] == sha(protocol_path)
    assert result['source_sha256'] == protocol['source_sha256']
    assert protocol['source_sha256'] == {name: sha(path) for name, path in files.items()}
    assert result['peak_self_rss_raw'] < protocol['resource_envelope']['rss_boundary_bytes']
    geo = json.loads(GEOMETRY.read_text())
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    reverse = json.loads((SOURCE / 'tensor_audit_result.json').read_text())
    group = json.loads((SOURCE / 'audit_result_v2.json').read_text())
    assert reverse['status'] == 'PASS_REVERSE_ORDER_FULL_CUBE_AUDIT'
    assert group['status'] == 'PASS_INTERPOLATED_SWEEP_GROUP_AUDIT'
    def product(slot, source_mask):
        out = 0
        for i, basis in enumerate(geo['blocks'][slot]['product_basis']):
            if source_mask >> i & 1:
                out ^= basis
        return out
    valid = [set(product(slot, mask) for mask in geo['permitted_canonical_a'])
             for slot in range(3)]
    assert all(len(values) == 40 for values in valid)
    qspan = {0}
    for basis in geo['blocks'][1]['product_basis']:
        qspan |= {value ^ basis for value in list(qspan)}
    assert len(qspan) == 128
    rows = []
    for panel in result['panels']:
        label = panel['label']
        assert panel['p_r_cells'] == 1600
        assert panel['qspan_size'] == 128 and panel['valid_q_count'] == 40
        assert sum(panel['phase_ns'].values()) <= panel['query_ns']
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())['coefficient_terms']
        triples = []
        for cell in panel['gcd_positive_cells']:
            p, r = cell['first_product'], cell['third_product']
            assert p in valid[0] and r in valid[2]
            for q in cell['qspan_roots']:
                assert q in qspan
                assert evaluate(tensor, p, q, r) == 0
                if q in valid[1]:
                    triples.append([p, q, r])
        assert sorted(triples) == sorted(panel['usable_triples'])
        prior = next(x for x in sweep['panels'] if x['name'] == label)
        assert sorted(triples) == sorted(x['products'] for x in prior['zero_triples'])
        independent_count = next(x['zeros'] for x in reverse['panels'] if x['name'] == label)
        assert len(triples) == independent_count
        rows.append({'label': label, 'cells': 1600, 'positive_cells': len(panel['gcd_positive_cells']),
                     'source_triples': len(triples), 'query_ns': panel['query_ns']})
    receipt = {'status': 'PASS_INDEPENDENT_QSPAN_GCD_REPLAY', 'rows': rows,
               'result_sha256': sha(result_path),
               'reverse_audit_sha256': sha(SOURCE / 'tensor_audit_result.json'),
               'group_audit_sha256': sha(SOURCE / 'audit_result_v2.json'),
               'verifier_sha256': sha(Path(__file__))}
    (HERE / 'verification_v2.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(receipt['status'], rows)


if __name__ == '__main__':
    main()
