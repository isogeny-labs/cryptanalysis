"""Recompute every frozen affine-span block and audit proof receipts."""
import hashlib
import json
from pathlib import Path

from probe import BinaryField, block_record, load_n41, source_basis

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, expected in cfg['sources'].items():
        source = Path(name)
        if not source.is_absolute():
            source = WORKSPACE / source
        assert sha(source) == expected, name
    result = json.loads((HERE / 'result.json').read_text())
    assert result['status'] == 'PASS_RESULTANT_BLOCK_SPAN_PROBE'
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    F41 = BinaryField(41, (1 << 3) | 1)
    B41 = source_basis(F41, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], 112, [12, 24])
    _, rows41 = load_n41(WORKSPACE / cfg['n41_input'])
    F131 = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    seed_mask = 898618
    bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
    B131 = source_basis(F131, bits, seed_mask << 1, [0, 18])
    source131 = json.loads((WORKSPACE / cfg['n131_input']).read_text())
    rows131 = [{'terms': [tuple(term) for term in row['terms']]}
               for row in source131['rows']]
    cases = result['cases']
    for recorded in cases:
        degree = recorded['field_degree']
        F, bases, terms = ((F41, B41, rows41[recorded['target_index']]['terms'])
                           if degree == 41 else
                           (F131, B131, rows131[recorded['target_index']]['terms']))
        actual = block_record(F, terms, *bases, *recorded['base_codes'],
                              recorded['width_each'], recorded['label'])
        actual.update(field_degree=degree, target_index=recorded['target_index'])
        assert actual == recorded, (degree, recorded['target_index'], recorded['label'])
    assert len(cases) == 185
    assert result['summary']['131']['4'] == {
        'random_cases': 16, 'rejected': 16, 'min_rank': 120, 'max_rank': 120}
    assert result['summary']['131']['5'] == {
        'random_cases': 16, 'rejected': 0, 'min_rank': 131, 'max_rank': 131}
    assert result['summary']['41']['2'] == {
        'random_cases': 16, 'rejected': 16, 'min_rank': 15, 'max_rank': 15}
    assert result['summary']['41']['3'] == {
        'random_cases': 16, 'rejected': 0, 'min_rank': 41, 'max_rank': 41}
    assert all(row['zero_in_affine_span'] for row in cases
               if row['label'] == 'positive_code_family' and row['target_index'] == 0)
    lean = (HERE / 'lean_check.log').read_text()
    assert "depends on axioms: [propext, Quot.sound]" in lean
    assert 'sorryAx' not in lean and 'error:' not in lean
    code = (HERE / 'AffineSpanSound.lean').read_text()
    assert all(word not in code for word in ('sorry', 'admit', 'axiom '))
    print(json.dumps({'status': 'PASS_BLOCK_SPAN_REPLAY',
                      'cases': len(cases), 'n131_width4_rejected': 16,
                      'n131_width5_rejected': 0,
                      'lean': 'CHECKED'}, sort_keys=True))


if __name__ == '__main__':
    main()
