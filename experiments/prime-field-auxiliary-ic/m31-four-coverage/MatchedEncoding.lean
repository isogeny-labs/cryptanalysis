import Lean

namespace M31MatchedEncoding
open Lean

private def ticks (row : Json) : Except String Nat := do
  let n ← (← row.getObjVal? "ic_observed_total_s").getNum?
  if n.mantissa < 0 || n.exponent > 4 then throw "unexpected timer precision"
  return n.mantissa.toNat * 10^(4 - n.exponent)

private def compareArms (arms : Json) (a b : String) : Except String (Bool × Nat × Nat) := do
  let c ← arms.getObjVal? a
  let d ← arms.getObjVal? b
  let fields := ["columns_blake3", "queries", "matrix_rank", "relations", "scalar"]
  let same ← fields.mapM fun key => do
    let x ← c.getObjVal? key
    let y ← d.getObjVal? key
    return x == y
  let routes := (← (← c.getObjVal? "uses_circuit").getBool?) &&
    !(← (← d.getObjVal? "uses_circuit").getBool?)
  return (same.all id && routes, ← ticks c, ← ticks d)

elab "encodingPairs" : term => do
  let data ← Lean.ofExcept (Json.parse (include_str "../m34-and-3arm-20261119/end_to_end_solves_summary.json"))
  let targets ← Lean.ofExcept ((data.getObjVal? "e1_m2_5target_solves").bind Json.getArr?)
  let pairs := [("arm_A_auxiliary", "arm_B_same_base_direct"),
    ("arm_D_mul126_circuit", "arm_D_mul126_direct"),
    ("arm_E_torus7_circuit", "arm_E_torus7_direct")]
  let rows ← pairs.mapM fun (a,b) => targets.toList.mapM fun t =>
    Lean.ofExcept ((t.getObjVal? "arms").bind fun arms => compareArms arms a b)
  return toExpr rows

private def rows : List (List (Bool × Nat × Nat)) := encodingPairs

/-- A strict gap exceeding one printed tick survives independent rounding of
both durations to the nearest tick. Counts follow the order in encodingPairs. -/
theorem paired_totals :
    rows.map List.length = [5,5,5] ∧
    rows.flatten.all (fun p => p.1) = true ∧
    rows.map (fun r => (r.filter (fun (_,c,d) => d + 1 < c)).length) = [5,1,5] ∧
    rows.map (fun r => (r.filter (fun (_,c,d) => c + 1 < d)).length) = [0,4,0] := by
  decide +kernel

end M31MatchedEncoding
