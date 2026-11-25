import Std

namespace M31TotalIndex

variable {Key Index Slot : Type} [DecidableEq Key]

-- The table returns a valid index at every address. Stored keys must
-- round-trip; all other addresses may contain any valid index.
def lookup (key : Index → Key) (address : Key → Slot) (table : Slot → Index)
    (x : Key) : Option Index :=
  let i := table (address x)
  if key i = x then some i else none

theorem exact (key : Index → Key) (address : Key → Slot) (table : Slot → Index)
    (stored : ∀ i, table (address (key i)) = i) (x : Key) (i : Index) :
    lookup key address table x = some i ↔ key i = x := by
  constructor
  · intro h
    simp only [lookup] at h
    split at h
    · cases h
      assumption
    · contradiction
  · rintro rfl
    simp [lookup, stored]

theorem absent (key : Index → Key) (address : Key → Slot) (table : Slot → Index)
    (stored : ∀ i, table (address (key i)) = i) (x : Key) :
    lookup key address table x = none ↔ ∀ i, key i ≠ x := by
  constructor
  · intro h i eq
    have hit := (exact key address table stored x i).2 eq
    rw [h] at hit
    contradiction
  · intro no
    simp [lookup, no]

end M31TotalIndex
