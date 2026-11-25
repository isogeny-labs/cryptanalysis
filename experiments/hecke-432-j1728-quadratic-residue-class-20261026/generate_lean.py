"""Generate exact Lean finite splitting-table checks."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'result.json').read_text())
lines = [
    'import Mathlib.Tactic.Ring', '', 'namespace J1728QuadraticResidues', '',
    '/-- A square unit makes the normalized quadratic split. -/',
    'theorem quadratic_split_identity {R : Type*} [CommRing R] (x u y : R)',
    '    (hy : y ^ 2 = u) : x ^ 2 - u = (x - y) * (x + y) := by',
    '  rw [← hy]',
    '  ring', '', '#print axioms quadratic_split_identity', '',
    'structure PlaceRow where',
    '  residueDegree : Nat',
    '  leftSplit : Bool',
    '  rightSplit : Bool', '',
    'def extensionDegrees (rows : List PlaceRow) (left : Bool) : List Nat :=',
    '  rows.flatMap fun row =>',
    '    if (if left then row.leftSplit else row.rightSplit) then',
    '      [row.residueDegree, row.residueDegree]',
    '    else [2 * row.residueDegree]', '',
    'def splitCount (rows : List PlaceRow) (left : Bool) : Nat :=',
    '  (rows.filter fun row => if left then row.leftSplit else row.rightSplit).length', '',
]
for row in result['rows']:
    p = row['prime']
    entries = ', '.join(
        '{ residueDegree := %s, leftSplit := %s, rightSplit := %s }' %
        (v['residue_degree'], str(v['left']['residue_square']).lower(),
         str(v['right']['residue_square']).lower()) for v in row['places'])
    lines += [f'def prime_{p}_places : List PlaceRow := [{entries}]', '',
              f'/-- Exact split and inert counts above {p} for both quadratic factors. -/',
              f'theorem prime_{p}_table_check :',
              f'    splitCount prime_{p}_places true = {row["left_split_places"]} ∧',
              f'    splitCount prime_{p}_places false = {row["right_split_places"]} ∧',
              f'    (extensionDegrees prime_{p}_places true).length = {row["left_split_places"]*2+row["left_inert_places"]} ∧',
              f'    (extensionDegrees prime_{p}_places false).length = {row["right_split_places"]*2+row["right_inert_places"]} ∧',
              f'    (extensionDegrees prime_{p}_places true).sum = 72 ∧',
              f'    (extensionDegrees prime_{p}_places false).sum = 72 := by',
              '  decide', '', f'#print axioms prime_{p}_table_check', '']
lines += ['end J1728QuadraticResidues', '']
(HERE / 'formal/QuadraticResidueTables.lean').write_text('\n'.join(lines))
