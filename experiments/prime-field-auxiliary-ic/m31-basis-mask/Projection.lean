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

abbrev Table := BitVec 13 → BitVec 32

def writeKey (t : Table) (a : BitVec 31) : Table :=
  fun i => if i = slot a then a.setWidth 32 else t i

private theorem untouched (keys : List (BitVec 31)) (t : Table) (i : BitVec 13)
    (absent : i ∉ keys.map slot) : keys.foldl writeKey t i = t i := by
  induction keys generalizing t with
  | nil => rfl
  | cons a tail ih =>
    simp only [List.map_cons, List.mem_cons, not_or] at absent
    rw [List.foldl_cons, ih _ absent.2]
    simp [writeKey, absent.1]

/-- Sequential writes refine the abstract slot contents for distinct labels. -/
theorem writes_refine_entry (keys : List (BitVec 31)) (t : Table) (i : BitVec 13)
    (distinct : (keys.map slot).Nodup) :
    keys.foldl writeKey t i =
      ((entry keys i).map (fun a => a.setWidth 32)).getD (t i) := by
  induction keys generalizing t with
  | nil => rfl
  | cons a tail ih =>
    rw [List.map_cons, List.nodup_cons] at distinct
    by_cases h : slot a = i
    · subst i
      rw [List.foldl_cons, untouched tail _ _ distinct.1]
      simp [writeKey, entry]
    · rw [List.foldl_cons, ih _ distinct.2]
      simp [entry, writeKey, h, Ne.symm h]

theorem sentinel_membership (x : BitVec 31) :
    coordinates.foldl writeKey (fun _ => 0xffffffff) (slot x) = x.setWidth 32 ↔
      x ∈ coordinates := by
  rw [writes_refine_entry _ _ _ frozen_slots_distinct, ← frozen_membership]
  cases e : entry coordinates (slot x) with
  | none =>
    simp only [Option.map_none, Option.getD_none, reduceCtorEq, iff_false]
    bv_decide
  | some a =>
    simp only [Option.map_some, Option.getD_some, Option.some.injEq]
    bv_decide

end M31Projection
