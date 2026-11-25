import Lean
import Mathlib.Tactic

namespace M31WalkShare

open Lean

private def nanoseconds (obj : Json) (key : String) (digits : Nat) : Except String Nat := do
  let n ← (← obj.getObjVal? key).getNum?
  if n.mantissa < 0 || n.exponent > digits then throw "unrepresentable interval"
  return n.mantissa.toNat * 10^(digits-n.exponent)

private def walkGroup (m : Nat) (arms : Json) : Except String (List (Nat × Nat × Nat)) := do
  (← arms.getObj?).toList.mapM fun (_, r) => do
    let walk ← nanoseconds r "target_walk_s" 9
    let total ← nanoseconds r "ic_observed_total_s" 9
    return (m, walk + 50000, total - 50000)

elab "archivedWalkRows" : term => do
  let data ← Lean.ofExcept (Json.parse (include_str "../m34-and-3arm-20261119/end_to_end_solves_summary.json"))
  let targets ← Lean.ofExcept ((data.getObjVal? "e1_m2_5target_solves").bind Json.getArr?)
  let two ← targets.toList.mapM fun (t : Json) => Lean.ofExcept ((t.getObjVal? "arms").bind (walkGroup 2))
  let higher ← Lean.ofExcept (data.getObjVal? "e1_m3_m4_solves_T0")
  let three ← Lean.ofExcept ((higher.getObjVal? "m3").bind (walkGroup 3))
  let four ← Lean.ofExcept ((higher.getObjVal? "m4").bind (walkGroup 4))
  return toExpr (two.flatten ++ three ++ four)

private def walkRows : List (Nat × Nat × Nat) := archivedWalkRows

/-- Bounds in parts per million after independent half-unit rounding allowances. -/
theorem archived_walk_share :
    (walkRows.filter (fun (m,_,_) => m == 2)).length = 37 ∧
    (walkRows.filter (fun (m,_,_) => m == 3)).length = 5 ∧
    (walkRows.filter (fun (m,_,_) => m == 4)).length = 4 ∧
    walkRows.all (fun (m,w,t) =>
      1000000*w < (if m = 2 then 11705 else if m = 3 then 188 else 9)*t) = true := by
  decide +kernel

end M31WalkShare
