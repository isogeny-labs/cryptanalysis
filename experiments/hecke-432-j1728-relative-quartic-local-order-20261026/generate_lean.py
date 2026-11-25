"""Generate Lean checks for the exact local index valuation tables."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
screen = json.loads((HERE / 'result.json').read_text())
audit = json.loads((HERE / 'audit.json').read_text())
audited = {r['prime']: r for r in audit['rows']}
lines = [
    'import Mathlib.Tactic.NormNum', '', 'namespace J1728QuarticLocalTables', '',
    'structure PlaceRow where',
    '  residueDegree : Nat',
    '  leftPolynomialValuation : Nat',
    '  rightPolynomialValuation : Nat', '',
    'def allEven (rows : List PlaceRow) : Bool :=',
    '  rows.all fun row => row.leftPolynomialValuation % 2 == 0 &&',
    '                       row.rightPolynomialValuation % 2 == 0', '',
    'def positiveCount (rows : List PlaceRow) (left : Bool) : Nat :=',
    '  (rows.filter fun row => if left then 0 < row.leftPolynomialValuation',
    '                         else 0 < row.rightPolynomialValuation).length', '',
    'def weightedIndex (rows : List PlaceRow) (left : Bool) : Nat :=',
    '  rows.foldl (fun total row => total + row.residueDegree *',
    '    (if left then row.leftPolynomialValuation / 2',
    '     else row.rightPolynomialValuation / 2)) 0', '',
]
for r in screen['rows']:
    p = r['prime']
    a = audited[p]
    values = ', '.join(
        '{ residueDegree := %s, leftPolynomialValuation := %s, rightPolynomialValuation := %s }' %
        (v['residue_degree'], v['left']['discriminant_valuation'],
         v['right']['discriminant_valuation']) for v in r['places'])
    lines += [f'def prime_{p}_places : List PlaceRow := [{values}]', '',
              f'/-- Exact local index table at rational prime {p}, given zero maximal discriminant. -/',
              f'theorem prime_{p}_index_table :',
              f'    allEven prime_{p}_places = true ∧',
              f'    positiveCount prime_{p}_places true = {a["positive_index_places"][0]} ∧',
              f'    positiveCount prime_{p}_places false = {a["positive_index_places"][1]} ∧',
              f'    weightedIndex prime_{p}_places true = {a["weighted_order_index_exponents"][0]} ∧',
              f'    weightedIndex prime_{p}_places false = {a["weighted_order_index_exponents"][1]} := by',
              '  decide', '', f'#print axioms prime_{p}_index_table', '']
lines += ['end J1728QuarticLocalTables', '']
(HERE / 'formal/QuarticLocalTables.lean').write_text('\n'.join(lines))
