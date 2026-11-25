"""Generate Lean statements for the exact local valuation parity tables."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'result.json').read_text())
lines = [
    'import Mathlib.Tactic.Ring', '', 'namespace J1728QuadraticLocal', '',
    '/-- Completing the square exposes the quadratic discriminant. -/',
    'theorem quadratic_square_identity {R : Type*} [CommRing R] (x b c : R) :',
    '    (2 * x + b) ^ 2 - (b ^ 2 - 4 * c) = 4 * (x ^ 2 + b * x + c) := by',
    '  ring', '', '#print axioms quadratic_square_identity', '',
    'structure PlaceRow where',
    '  residueDegree : Nat',
    '  leftValuation : Nat',
    '  rightValuation : Nat',
    '  leftIndex : Nat',
    '  rightIndex : Nat', '',
    'def allEven (rows : List PlaceRow) : Bool :=',
    '  rows.all fun row => row.leftValuation % 2 == 0 && row.rightValuation % 2 == 0', '',
    'def allIndex (rows : List PlaceRow) : Bool :=',
    '  rows.all fun row => row.leftIndex == row.leftValuation / 2 &&',
    '                       row.rightIndex == row.rightValuation / 2', '',
    'def weightedLeft (rows : List PlaceRow) : Nat :=',
    '  rows.foldl (fun total row => total + row.residueDegree * row.leftValuation) 0', '',
    'def weightedRight (rows : List PlaceRow) : Nat :=',
    '  rows.foldl (fun total row => total + row.residueDegree * row.rightValuation) 0', '',
]
for row in result['rows']:
    p = row['prime']
    entries = ', '.join(
        '{ residueDegree := %s, leftValuation := %s, rightValuation := %s, leftIndex := %s, rightIndex := %s }' %
        (v['residue_degree'], v['left_discriminant_valuation'], v['right_discriminant_valuation'],
         v['left_local_order_index_exponent'], v['right_local_order_index_exponent'])
        for v in row['places'])
    lines += [f'def prime_{p}_places : List PlaceRow := [{entries}]', '',
              f'/-- Exact quadratic discriminant parity and norm weights at rational prime {p}. -/',
              f'theorem prime_{p}_table_check :',
              f'    allEven prime_{p}_places = true ∧',
              f'    allIndex prime_{p}_places = true ∧',
              f'    weightedLeft prime_{p}_places = {row["weighted_discriminant_valuations"][0]} ∧',
              f'    weightedRight prime_{p}_places = {row["weighted_discriminant_valuations"][1]} := by',
              '  decide', '', f'#print axioms prime_{p}_table_check', '']
lines += ['end J1728QuadraticLocal', '']
(HERE / 'formal/QuadraticLocal.lean').write_text('\n'.join(lines))
