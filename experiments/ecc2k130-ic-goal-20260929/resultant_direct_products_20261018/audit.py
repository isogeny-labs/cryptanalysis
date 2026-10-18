"""Read-only independent field replay of direct four-product receipts."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'resultant_block_span_20261018'))
from probe import BinaryField, evaluate, source_basis, product, load_n41


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


cfg = read('protocol.json')
for name, expected in cfg['sources'].items():
    source = Path(name)
    if not source.is_absolute():
        source = WORKSPACE / source
    assert sha(source) == expected, name
gate = read('n131_gate.json')
assert gate['status'] == 'FROZEN_AFTER_N41_DIRECT_REPLAY'
for name, expected in gate['sources'].items():
    source = Path(name)
    if not source.is_absolute():
        source = WORKSPACE / source
    assert sha(source) == expected, name

F41 = BinaryField(41, (1 << 3) | 1)
sources41, rows41 = load_n41(WORKSPACE / cfg['n41_input'])
F131 = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
seed_mask = 898618
bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
basis131 = source_basis(F131, bits, seed_mask << 1, [0, 18])
source131 = json.loads((WORKSPACE / cfg['n131_input']).read_text())
terms131 = [[tuple(item) for item in row['terms']] for row in source131['rows']]

for degree, count in ((41, 562), (131, 150)):
    result = read(f'n{degree}_result.json')
    run = read(f'n{degree}_run_result.json')
    roots = read(f'n{degree}_root_result.json')
    assert result['status'] == 'PASS_DIRECT_FOUR_PRODUCT_REPLAY'
    assert result['protocol_sha256'] == run['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert run['status'] == 'COMPLETE' and run['stop_reason'] is None
    assert run['sampled_peak_combined_rss_bytes'] < cfg['rss_cap_bytes']
    assert run['stdout_sha256'] == sha(HERE / f'n{degree}.stdout')
    assert run['stderr_sha256'] == sha(HERE / f'n{degree}.stderr')
    assert len(result['rows']) == len(roots['rows']) == count
    reference = {(row['target_index'], row['first_code']): row
                 for row in roots['rows']}
    for row in result['rows']:
        index, code = row['target_index'], row['first_code']
        assert row['exceptions'] == []
        assert len(row['q_products']) == len(set(row['q_products'])) == 4
        assert row['span_root_hits'] == reference[(index, code)]['span_root_hits']
        if degree == 41:
            F, p, terms = F41, sources41[code][0], rows41[index]['terms']
        else:
            F, p, terms = F131, product(basis131[0], code), terms131[index]
        for q in row['q_products']:
            assert evaluate(F, terms, p, q) == 0
    assert result['first_codes'] == (281 if degree == 41 else 75)

lean = (HERE / 'lean_check.log').read_text()
assert 'product_from_residual' in lean
assert 'sorryAx' not in lean and 'error:' not in lean
code = (HERE / 'DirectProductLaw.lean').read_text()
assert all(word not in code for word in ('sorry', 'admit', 'axiom '))
print(json.dumps({'status': 'PASS_DIRECT_PRODUCT_FROZEN_AUDIT',
                  'n41_quartics': 562, 'n131_quartics': 150,
                  'all_four_distinct_roots': True, 'lean': 'CHECKED'}, sort_keys=True))
