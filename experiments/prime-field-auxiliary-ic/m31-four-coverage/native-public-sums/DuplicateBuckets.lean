import Mathlib.Data.Finset.Card

namespace DuplicateBuckets

variable {I K : Type*}

/-- Count only the indices that have survived the preceding passes. -/
def pass (key : I → K) (tag : K → ℕ) (s : Finset I) : Finset I :=
  s.filter fun i => 1 < (s.filter fun j => tag (key j) = tag (key i)).card

private theorem keep_iff (key : I → K) (tag : K → ℕ) (s : Finset I)
    {i j : I} (distinct : i ≠ j) (equal : key i = key j) :
    (i ∈ pass key tag s ∧ j ∈ pass key tag s) ↔ i ∈ s ∧ j ∈ s := by
  constructor
  · intro h
    exact ⟨(Finset.mem_filter.mp h.1).1, (Finset.mem_filter.mp h.2).1⟩
  · rintro ⟨hi,hj⟩
    have enough : 1 < (s.filter fun k => tag (key k) = tag (key i)).card :=
      Finset.one_lt_card.mpr ⟨i, Finset.mem_filter.mpr ⟨hi,rfl⟩,
        j, Finset.mem_filter.mpr ⟨hj,congrArg tag equal.symm⟩, distinct⟩
    exact ⟨Finset.mem_filter.mpr ⟨hi,enough⟩, Finset.mem_filter.mpr ⟨hj,equal ▸ enough⟩⟩

/-- Every equal-key pair of distinct original indices survives any finite
sequence of bucket passes, including a sequence with no passes. -/
theorem pairs_iff (key : I → K) (tags : List (K → ℕ)) (s : Finset I)
    {i j : I} (distinct : i ≠ j) (equal : key i = key j) :
    let kept := tags.foldl (fun t tag => pass key tag t) s
    (i ∈ kept ∧ j ∈ kept) ↔ i ∈ s ∧ j ∈ s := by
  induction tags generalizing s with
  | nil => rfl
  | cons tag rest ih =>
    exact (ih (pass key tag s)).trans (keep_iff key tag s distinct equal)

private theorem subset (key : I → K) (tags : List (K → ℕ)) (s : Finset I) :
    tags.foldl (fun t tag => pass key tag t) s ⊆ s := by
  induction tags generalizing s with
  | nil => exact fun _ h => h
  | cons tag rest ih =>
    exact (ih (pass key tag s)).trans (Finset.filter_subset _ _)

/-- A repeated value retains its entire original group, regardless of multiplicity. -/
theorem group_eq [DecidableEq K] (key : I → K) (tags : List (K → ℕ)) (s : Finset I)
    (v : K) (h : 1 < (s.filter fun i => key i = v).card) :
    ((tags.foldl (fun t tag => pass key tag t) s).filter fun i => key i = v) =
      s.filter fun i => key i = v := by
  obtain ⟨a,ha,b,hb,hab⟩ := Finset.one_lt_card.mp h
  obtain ⟨ha,ea⟩ := Finset.mem_filter.mp ha
  obtain ⟨hb,eb⟩ := Finset.mem_filter.mp hb
  ext i
  simp only [Finset.mem_filter]
  constructor
  · exact fun h => ⟨subset key tags s h.1,h.2⟩
  · rintro ⟨hi,ei⟩
    by_cases e : i = a
    · subst i
      exact ⟨((pairs_iff key tags s hab (ea.trans eb.symm)).mpr ⟨ha,hb⟩).1,ea⟩
    · exact ⟨((pairs_iff key tags s e (ei.trans ea.symm)).mpr ⟨hi,ha⟩).1,ei⟩

/-- The two tags used on the packed 62-bit M31 coordinate key. -/
def coordinateTags : List (ℕ → ℕ) :=
  [fun k => k % 2^18, fun k => (k / 2^31) % 2^18]

#print axioms pairs_iff
#print axioms group_eq
end DuplicateBuckets
