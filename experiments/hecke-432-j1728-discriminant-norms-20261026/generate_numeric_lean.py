"""Emit exact Lean statements for the saved discriminant norm integers."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / 'relative_result.json').read_text())['rows']
lines = ['import Mathlib.Tactic.NormNum', '', 'namespace J1728DiscriminantNorms', '']
for row in rows:
    degree = row['base_degree']
    norm = row['relative_discriminant_norm_numerator']
    root = row['relative_discriminant_sixth_root']
    lines += [f'/-- Exact degree-{degree} relative discriminant norm certificate. -/',
              f'theorem relative_{degree}_sixth_power :',
              f'    ({norm} : ℕ) = ({root} : ℕ) ^ 6 := by',
              '  norm_num', '', f'#print axioms relative_{degree}_sixth_power', '']
lines += ['end J1728DiscriminantNorms', '']
(HERE / 'formal/NumericDiscriminants.lean').write_text('\n'.join(lines))
