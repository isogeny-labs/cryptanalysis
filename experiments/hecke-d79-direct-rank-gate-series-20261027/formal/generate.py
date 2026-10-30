"""Generate a Lean certificate of the frozen gate logic on audited ranks."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
audit=json.loads((HERE.parent/'audit.json').read_text())
assert audit['status']=='PASS' and len(audit['cases'])==4
pairs=[(x['baseline_rank_mod_q'],x['full_pool_rank_mod_q']) for x in audit['cases']]
assert pairs==[(32,34),(35,39),(31,34),(32,35)]
literal=', '.join(f'({a}, {b})' for a,b in pairs)
lines=['module','','public import Init','','namespace DirectRankGateSeries',
       f'public def rankPairs : List (Nat × Nat) := [{literal}]',
       'public def falseReject (x : Nat × Nat) : Bool := x.1 < 37 && x.2 >= 39',
       'public theorem one_false_reject :',
       '    (rankPairs.filter falseReject).length = 1 := by decide',
       'public theorem p103357_gate_counterexample :',
       '    falseReject (35, 39) = true := by decide',
       'public theorem three_correct_rejections :',
       '    (rankPairs.filter (fun x => x.1 < 37 && x.2 < 39)).length = 3 := by decide',
       '#print axioms one_false_reject',
       '#print axioms p103357_gate_counterexample',
       '#print axioms three_correct_rejections',
       'end DirectRankGateSeries','']
(HERE/'DirectRankGateSeries.lean').write_text('\n'.join(lines))
print('generated audited rank pairs',pairs)
