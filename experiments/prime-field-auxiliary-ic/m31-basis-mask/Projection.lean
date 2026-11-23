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

/-- The high 13 bits of the C++ wrapping 32-bit product. -/
def slot (x : BitVec 31) : BitVec 13 :=
  (((x.setWidth 32) * (0x9e6002cb : BitVec 32)) >>> 19).setWidth 13

set_option maxRecDepth 50000 in
set_option maxHeartbeats 8000000 in
theorem frozen_slots_distinct : (coordinates.map slot).Nodup := by decide +kernel

/-- Contents of a slot initialized empty and populated by the given keys. -/
def entry (keys : List (BitVec 31)) (i : BitVec 13) : Option (BitVec 31) :=
  keys.find? (fun x => slot x == i)

theorem entry_exact (keys : List (BitVec 31)) (distinct : (keys.map slot).Nodup)
    (x : BitVec 31) : entry keys (slot x) = some x ↔ x ∈ keys := by
  induction keys with
  | nil => simp [entry]
  | cons a tail ih =>
    rw [List.map_cons, List.nodup_cons] at distinct
    by_cases h : slot a = slot x
    · have absent : x ∉ tail := fun hx => distinct.1 (List.mem_map.mpr ⟨x, hx, h.symm⟩)
      simp [entry, h, absent, eq_comm]
    · have neq : x ≠ a := fun e => h (congrArg slot e.symm)
      simpa [entry, List.find?_cons, h, neq] using ih distinct.2

theorem frozen_membership (x : BitVec 31) :
    entry coordinates (slot x) = some x ↔ x ∈ coordinates :=
  entry_exact coordinates frozen_slots_distinct x

end M31Projection
