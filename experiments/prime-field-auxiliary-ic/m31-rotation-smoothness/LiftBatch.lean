import Std

namespace M31LiftBatch

/-- One update of a single smoothness band's pending queue. Its entries are
already eligible, so a flush needs only the lift predicate. -/
def step (eligible lift : α → Bool) (pending orbit : List α) : Nat × List α :=
  let xs := pending ++ orbit.filter eligible
  if xs.length ≥ 128 then ((xs.take 128).countP lift, xs.drop 128) else (0, xs)

/-- Charging the live tail at the end recovers exactly the direct lift count.
The identity also applies when the prior batch is empty or the new orbit
contains no eligible coordinates. -/
theorem accounting (eligible lift : α → Bool) (pending orbit : List α) :
    (step eligible lift pending orbit).1 +
      (step eligible lift pending orbit).2.countP lift =
    pending.countP lift + orbit.countP (fun x => lift x && eligible x) := by
  dsimp only [step]
  split
  · simp only
    rw [← List.countP_append, List.take_append_drop, List.countP_append, List.countP_filter]
  · simp [List.countP_filter]

/-- A single flush suffices, and each tentative write during compaction
fits in the native band's 159 slots, including writes for rejected lanes. -/
theorem bounds (eligible lift : α → Bool) (pending orbit : List α)
    (hp : pending.length < 128) (ho : orbit.length ≤ 31) :
    (∀ i < orbit.length, pending.length + i < 159) ∧
    (step eligible lift pending orbit).2.length < 128 := by
  have hf := List.length_filter_le eligible orbit
  constructor
  · omega
  · dsimp only [step]
    split <;> simp_all only [List.length_append, List.length_drop] <;> omega

end M31LiftBatch
