"""Generate finite Lean support-composition checks from audited rows."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
audit=json.loads((ROOT/'audit.json').read_text())
gate=json.loads((ROOT/'gate-result.json').read_text())
assert audit['status']=='PASS' and audit['p']==gate['p']==90917
supports=audit['hecke_candidate_supports']
residues=gate['selected']['projection_residues']
assert len(supports)==201 and len(residues)==40
lines=['module','','public import Init','','namespace DirectRankGate',
       'public def residues : Array Nat := #['+', '.join(map(str,residues))+']',
       'public def supports : List (List Nat) := [']
lines += ['  ['+', '.join(map(str,s))+'],' for s in supports]
lines += [']',
          'public def ones (s : List Nat) : Nat := (s.map fun i => residues[i]!).sum',
          'set_option maxRecDepth 32768',
          'set_option maxHeartbeats 1000000',
          'public theorem support3_count :',
          '    (supports.filter (fun s => s.length == 3)).length = 1 := by decide',
          'public theorem support4_count :',
          '    (supports.filter (fun s => s.length == 4)).length = 200 := by decide',
          'public theorem mixed_residue_count :',
          '    (supports.filter (fun s => ones s == 2)).length = 197 := by decide',
          'public theorem zero_residue_count :',
          '    (supports.filter (fun s => ones s == 0)).length = 3 := by decide',
          'public theorem four_residue_count :',
          '    (supports.filter (fun s => ones s == 4)).length = 1 := by decide',
          '#print axioms support3_count',
          '#print axioms support4_count',
          '#print axioms mixed_residue_count',
          '#print axioms zero_residue_count',
          '#print axioms four_residue_count',
          'end DirectRankGate','']
(HERE/'DirectRankGate.lean').write_text('\n'.join(lines))
print('generated',len(supports),'support rows')
