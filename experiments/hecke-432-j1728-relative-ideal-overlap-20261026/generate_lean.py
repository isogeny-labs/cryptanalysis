"""Emit Lean checks for each saved finite prime-ideal valuation table."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'result.json').read_text())
lines = [
    'import Mathlib.Tactic.NormNum', '', 'namespace J1728IdealOverlap', '',
    'structure PlaceRow where',
    '  residueDegree : Nat',
    '  relativeValuation : Nat',
    '  resultantValuation : Nat', '',
    'def overlapCount (rows : List PlaceRow) : Nat :=',
    '  (rows.filter fun row => decide (0 < row.relativeValuation ∧ 0 < row.resultantValuation)).length', '',
    'def weightedRelative (rows : List PlaceRow) : Nat :=',
    '  rows.foldl (fun total row => total + row.residueDegree * row.relativeValuation) 0', '',
    'def weightedResultant (rows : List PlaceRow) : Nat :=',
    '  rows.foldl (fun total row => total + row.residueDegree * row.resultantValuation) 0', '',
]
for factor in result['rows']:
    degree = factor['base_degree']
    for cell in factor['primes']:
        p = cell['prime']
        name = f'degree_{degree}_prime_{p}'
        entries = ', '.join(
            '{ residueDegree := %s, relativeValuation := %s, resultantValuation := %s }' %
            (v['residue_degree'], v['relative_discriminant_valuation'], v['pair_resultant_valuation'])
            for v in cell['places'])
        lines += [f'def {name} : List PlaceRow := [{entries}]', '',
                  f'/-- Exact saved valuation-table count and norm weights for degree {degree} at {p}. -/',
                  f'theorem {name}_check :',
                  f'    overlapCount {name} = {cell["overlap_place_count"]} ∧',
                  f'    weightedRelative {name} = {cell["weighted_relative_discriminant_valuation"]} ∧',
                  f'    weightedResultant {name} = {cell["weighted_pair_resultant_valuation"]} := by',
                  '  decide', '', f'#print axioms {name}_check', '']
lines += ['end J1728IdealOverlap', '']
(HERE / 'formal/IdealOverlapTables.lean').write_text('\n'.join(lines))
