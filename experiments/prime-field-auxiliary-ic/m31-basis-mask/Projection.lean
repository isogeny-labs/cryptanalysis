import Lean
import Std.Tactic.BVDecide

namespace M31Projection

/-- Expand the committed decimal lines to a literal list before kernel reduction. -/
elab "basisNumerals" : term => do
  let lines := ((include_str "coordinates.txt").trimAscii.toString).splitOn "\n"
  let values ← lines.mapM fun s => do
    let some n := s.toNat? | throwError "invalid decimal coordinate {s}"
    pure n
  return Lean.toExpr values

private def values : List Nat := basisNumerals
def coordinates := values.map (BitVec.ofNat 31)
def mask : BitVec 31 := 0x1520944e

theorem inputs_valid : values.length = 195 ∧
    values.all (fun n => decide (n < 2147483647)) = true := by decide +kernel

theorem distinguishes_iff_hits (a b m : BitVec 31) :
    (a &&& m) ≠ (b &&& m) ↔ ((a ^^^ b) &&& m) ≠ 0 := by
  bv_decide

/-- Adding positions cannot collapse labels already separated by the smaller mask. -/
theorem extend_separates (a b m extra : BitVec 31) (h : (a &&& m) ≠ (b &&& m)) :
    (a &&& (m ||| extra)) ≠ (b &&& (m ||| extra)) := by
  bv_decide

theorem width : ((List.range 31).filter (fun i => mask.getLsbD i)).length = 11 := by
  decide +kernel

set_option maxRecDepth 50000 in
set_option maxHeartbeats 8000000 in
theorem frozen_labels_distinct : (coordinates.map (fun x => x &&& mask)).Nodup := by
  decide +kernel

end M31Projection
