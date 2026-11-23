import Std.Tactic.BVDecide

namespace BatchSmooth

/-- Keep the original coordinate attached while updating its residual. -/
def pass (strip : Nat → Nat → Nat) (q : Nat) (lane : Nat × Nat) : Nat × Nat :=
  (lane.1, strip q lane.2)

theorem transpose_passes (strip : Nat → Nat → Nat) (qs : List Nat)
    (lanes : List (Nat × Nat)) :
    qs.foldl (fun rows q => rows.map (pass strip q)) lanes =
      lanes.map (fun lane => (lane.1, qs.foldl (fun v q => strip q v) lane.2)) := by
  induction qs generalizing lanes with
  | nil => simp
  | cons q qs ih =>
    simp [List.foldl_cons, ih, List.map_map, Function.comp_def, pass]

/-- Filtering pairs after the transposed passes preserves accepted coordinates,
including their order and multiplicity for a short final batch. -/
theorem stable_output (strip : Nat → Nat → Nat) (qs : List Nat)
    (lanes : List (Nat × Nat)) (keep : Nat × Nat → Bool) :
    ((qs.foldl (fun rows q => rows.map (pass strip q)) lanes).filter keep).map Prod.fst =
    (lanes.filter (fun lane => keep (lane.1, qs.foldl (fun v q => strip q v) lane.2))).map Prod.fst := by
  rw [transpose_passes]
  induction lanes with
  | nil => rfl
  | cons lane lanes ih =>
    cases h : keep (lane.1, qs.foldl (fun v q => strip q v) lane.2) <;>
      simp [h, ih]

/-- The C++ loop runs on a nonzero unsigned mask. Its count of trailing
zeros names a live lane. Clearing the lowest bit removes exactly that
lane, decreases the mask, and leaves the other bits untouched. -/
theorem clear_marked_lane (mask : BitVec 32) (live : mask ≠ 0) :
    let lane := mask.ctz
    let bit := (1 : BitVec 32) <<< lane
    let rest := mask &&& (mask - 1)
    (mask &&& bit) = bit ∧ bit ≠ 0 ∧
    (mask &&& (bit - 1)) = 0 ∧ rest = (mask ^^^ bit) ∧ rest < mask := by
  bv_decide

/-- Only the low 16 bits are populated by a batch. -/
theorem lane_in_batch (mask : BitVec 32) (live : mask ≠ 0) (bound : mask < 65536) :
    mask.ctz < 16 := by
  bv_decide

/-- One iteration of mask construction preserves the low-16-bit bound.
A probe sees the new predicate at the current lane and is unchanged
elsewhere, assuming the current lane was initially clear. -/
theorem insert_lane (mask lane probe : BitVec 32) (hit : Bool)
    (bound : mask < 65536) (index : lane < 16)
    (clear : mask &&& ((1 : BitVec 32) <<< lane) = 0) :
    let next := mask ||| ((if hit then (1 : BitVec 32) else 0) <<< lane)
    next < 65536 ∧ (next &&& ((1 : BitVec 32) <<< probe)) =
      (if probe = lane then (if hit then (1 : BitVec 32) <<< lane else 0)
       else mask &&& ((1 : BitVec 32) <<< probe)) := by
  bv_decide

/-- The full-word implementation can select lane 31, and every selected
lane is within its 32-element scratch array. -/
theorem lane_in_full_batch (mask : BitVec 32) (live : mask ≠ 0) :
    mask.ctz < 32 := by
  bv_decide

/-- Setting the flag for a fresh lane in a full word updates its
divisibility predicate without changing any other lane's flag. -/
theorem insert_full_lane (mask lane probe : BitVec 32) (hit : Bool)
    (index : lane < 32) (clear : mask &&& ((1 : BitVec 32) <<< lane) = 0) :
    let flag := (1 : BitVec 32) <<< lane
    let next := mask ||| (if hit then flag else 0)
    flag ≠ 0 ∧ (next &&& ((1 : BitVec 32) <<< probe)) =
      (if probe = lane then (if hit then flag else 0)
       else mask &&& ((1 : BitVec 32) <<< probe)) := by
  bv_decide

end BatchSmooth
