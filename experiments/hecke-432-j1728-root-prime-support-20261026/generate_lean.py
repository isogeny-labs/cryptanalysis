"""Emit exact Lean gcd statements for the frozen root integers."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE.parent / 'hecke-432-j1728-discriminant-norms-20261026/relative_result.json').read_text())
results = json.loads((HERE / 'result.json').read_text())
by_degree = {r['base_degree']: r for r in inputs['rows']}
lines = ['import Mathlib.Tactic.NormNum', '', 'namespace J1728RootSupport', '']
for r in results['rows']:
    degree = r['base_degree']
    source = by_degree[degree]
    a = source['relative_discriminant_sixth_root']
    b = source['pair_resultant_norm_cube_root']
    g = r['exact_common_gcd']
    lines += [f'/-- Exact common root gcd for the degree-{degree} base factor. -/',
              f'theorem degree_{degree}_root_gcd :',
              f'    Nat.gcd ({a} : ℕ) ({b} : ℕ) = {g} := by',
              '  norm_num', '', f'#print axioms degree_{degree}_root_gcd', '']
    product = ' * '.join(f'{p} ^ {e}' for p, e in r['complete_common_gcd_factorization'])
    lines += [f'/-- Complete integer factorization of the degree-{degree} root gcd. -/',
              f'theorem degree_{degree}_gcd_factors :',
              f'    ({g} : ℕ) = {product} := by',
              '  norm_num', '', f'#print axioms degree_{degree}_gcd_factors', '']
lines += ['end J1728RootSupport', '']
(HERE / 'formal/RootGcd.lean').write_text('\n'.join(lines))
