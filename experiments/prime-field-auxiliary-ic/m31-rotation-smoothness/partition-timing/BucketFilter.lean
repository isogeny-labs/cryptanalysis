import Mathlib.Data.Finset.Image
import Mathlib.Data.Finset.Filter

namespace M31BucketFilter

abbrev Oriented := ℕ × Bool

def buckets (h : ℕ → ℕ) (s : Finset Oriented) : Finset Oriented :=
  s.image fun e => (h e.1, e.2)

def retained (h : ℕ → ℕ) (s : Finset Oriented) : Finset Oriented :=
  s.filter fun e => ((h e.1, false) ∈ buckets h s ∧ (h e.1, true) ∈ buckets h s)

/-- For every hash function, retaining buckets observed in both orientations
preserves exactly the keys occurring with both orientations. -/
theorem preserves_pairs (h : ℕ → ℕ) (s : Finset Oriented) (k : ℕ) :
    ((k, false) ∈ retained h s ∧ (k, true) ∈ retained h s) ↔
    ((k, false) ∈ s ∧ (k, true) ∈ s) := by
  constructor
  · rintro ⟨a,b⟩
    exact ⟨(Finset.mem_filter.mp a).1, (Finset.mem_filter.mp b).1⟩
  · rintro ⟨a,b⟩
    have hf : (h k, false) ∈ buckets h s :=
      Finset.mem_image.mpr ⟨(k,false),a,rfl⟩
    have ht : (h k, true) ∈ buckets h s :=
      Finset.mem_image.mpr ⟨(k,true),b,rfl⟩
    exact ⟨Finset.mem_filter.mpr ⟨a,hf,ht⟩, Finset.mem_filter.mpr ⟨b,hf,ht⟩⟩

end M31BucketFilter
