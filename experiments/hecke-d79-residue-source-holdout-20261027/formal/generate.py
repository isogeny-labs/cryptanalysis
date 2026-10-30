"""Generate finite Lean checks for the audited p78157 support composition."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
audit=json.loads((ROOT/'audit.json').read_text())
cls=json.loads((ROOT/'class-result.json').read_text())['selected']
assert audit['status']=='PASS' and audit['p']==cls['p']==78157
supports=audit['hecke_candidate_supports']
residues=cls['projection_residues']
assert len(supports)==194 and len(residues)==40
lines=['module','','public import Init','','namespace ResidueSupport',
       'public def residues : Array Nat := #['+', '.join(map(str,residues))+']',
       'public def supports : List (Nat × Nat × Nat × Nat) := [']
lines += ['  ('+', '.join(map(str,s))+'),' for s in supports]
lines += [']',
          'public def ones (s : Nat × Nat × Nat × Nat) : Nat :=',
          '  residues[s.1]! + residues[s.2.1]! + residues[s.2.2.1]! + residues[s.2.2.2]!',
          'set_option maxRecDepth 32768',
          'set_option maxHeartbeats 1000000',
          'public theorem supports_strict :',
          '    supports.all (fun s => s.1 < s.2.1 && s.2.1 < s.2.2.1 &&',
          '      s.2.2.1 < s.2.2.2 && s.2.2.2 < 40) = true := by decide',
          'public theorem mixed_support_count :',
          '    (supports.filter (fun s => ones s == 2)).length = 193 := by decide',
          'public theorem zero_support_count :',
          '    (supports.filter (fun s => ones s == 0)).length = 1 := by decide',
          'public theorem all_one_support_count :',
          '    (supports.filter (fun s => ones s == 4)).length = 0 := by decide',
          '#print axioms supports_strict',
          '#print axioms mixed_support_count',
          '#print axioms zero_support_count',
          '#print axioms all_one_support_count',
          'end ResidueSupport','']
(HERE/'ResidueSupport.lean').write_text('\n'.join(lines))
print('generated',len(supports),'support rows')
