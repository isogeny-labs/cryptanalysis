import Init

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

end BatchSmooth
