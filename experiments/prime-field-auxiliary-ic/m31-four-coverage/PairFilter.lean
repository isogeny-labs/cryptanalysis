import Mathlib.Algebra.Group.Basic
import Mathlib.Data.Set.Image
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

namespace M31FourCoverage.PairFilter

variable {G H : Type*} [AddCommGroup G]

/-- Every prefix admitting a signed fourth step into the signed basis
hits the hash image of the two-step support, even for a constant hash. -/
theorem completion_bucket (S : Set G) (closed : ∀ b ∈ S, -b ∈ S)
    (hash : G → H) {t b : G} (hb : b ∈ S) (h : t+b ∈ S) :
    hash t ∈ hash '' {z | ∃ u ∈ S, ∃ v ∈ S, z = u+v} := by
  refine ⟨t, ?_, rfl⟩
  exact ⟨t+b, h, -b, closed b hb, by simp⟩

/-- Keeping a single representative of every global sign orbit suffices
when the key is unchanged by negation (as with an abscissa hash). -/
theorem oriented_image {T R : Set G} (subset : R ⊆ T)
    (cover : ∀ t ∈ T, t ∈ R ∨ -t ∈ R) (hash : G → H)
    (even : ∀ t, hash (-t) = hash t) : hash '' R = hash '' T := by
  apply Set.Subset.antisymm (Set.image_mono subset)
  rintro _ ⟨t, ht, rfl⟩
  rcases cover t ht with h | h
  · exact ⟨t, h, rfl⟩
  · exact ⟨-t, h, even t⟩

/-- Skipping a node with zero contribution preserves each histogram bin. -/
theorem count_preserved {I : Type*} (nodes : Finset I) (keep : I → Prop)
    [DecidablePred keep] (weight : I → ℕ)
    (sound : ∀ i ∈ nodes, weight i ≠ 0 → keep i) :
    ∑ i ∈ nodes.filter keep, weight i = ∑ i ∈ nodes, weight i := by
  apply Finset.sum_subset (Finset.filter_subset _ _)
  intro i hi hout
  by_contra hn
  exact hout (Finset.mem_filter.mpr ⟨hi, sound i hi hn⟩)

end M31FourCoverage.PairFilter
