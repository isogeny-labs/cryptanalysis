import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic

namespace M31Multiplicity

/-- For any finite table of descriptions, dropping all singleton fibers
from both populations preserves the excess of descriptions over outputs.
The resulting difference in ambiguity rates is stated with denominators
cleared. Here s counts singleton fibers, p occupied outputs, and m descriptions. -/
theorem sampling_gap (m p s : ℕ) (hsp : s ≤ p) (hpm : p ≤ m) :
    (m - s) * p = (p - s) * m + s * (m - p) := by
  zify [hsp, hpm, hsp.trans hpm]
  ring

/-- Sampling descriptions gives each output precisely its multiplicity
of preimages. -/
theorem preimage_count {C P : Type*} [Fintype C] [DecidableEq P]
    (f : C → P) (event : Finset P) :
    (Finset.univ.filter (fun c => f c ∈ event)).card =
      ∑ p ∈ event, (Finset.univ.filter (fun c => f c = p)).card := by
  classical
  let selected := Finset.univ.filter (fun c => f c ∈ event)
  have hmap : ∀ c ∈ selected, f c ∈ event := by simp [selected]
  calc
    _ = ∑ p ∈ event, (selected.filter (fun c => f c = p)).card :=
      Finset.card_eq_sum_card_fiberwise hmap
    _ = _ := by
      apply Finset.sum_congr rfl
      intro p hp
      congr 1
      ext c
      simp only [selected, Finset.mem_filter, Finset.mem_univ, true_and]
      exact ⟨And.right, fun h => ⟨h ▸ hp, h⟩⟩

#print axioms preimage_count
#print axioms sampling_gap
end M31Multiplicity
