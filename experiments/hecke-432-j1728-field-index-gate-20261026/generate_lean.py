"""Emit exact Lean arithmetic identities from the audited discriminants."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'result.json').read_text())
audit = json.loads((HERE / 'audit.json').read_text())
P = result['polynomial_discriminant']
D = result['field_discriminant']
I = result['order_index']
assert all(int(x) > 0 for x in (P, D, I))
index_product = ' * '.join(f'{p} ^ {e}' for p, e in audit['complete_index_factorization'])
lines = [
    'import Mathlib.Tactic.NormNum', '',
    'set_option exponentiation.threshold 512',
    'set_option maxRecDepth 4096', '',
    'namespace J1728FieldIndex', '',
    '/-- Exact defining-polynomial discriminant, field discriminant, and index identity. -/',
    'theorem polynomial_field_index_identity :',
    f'    ({P} : ℕ) = ({D} : ℕ) * ({I} : ℕ) ^ 2 := by',
    '  norm_num', '', '#print axioms polynomial_field_index_identity', '',
    '/-- Complete prime-power factorization of the source-field discriminant. -/',
    'theorem field_discriminant_factors :',
    f'    ({D} : ℕ) = 2 ^ 18 * 3 ^ 45 := by',
    '  norm_num', '', '#print axioms field_discriminant_factors', '',
    '/-- Complete prime-power factorization of the monogenic-order index. -/',
    'theorem order_index_factors :',
    f'    ({I} : ℕ) = {index_product} := by',
    '  norm_num', '', '#print axioms order_index_factors', '',
    'end J1728FieldIndex', '',
]
(HERE / 'formal/FieldIndex.lean').write_text('\n'.join(lines))
