import Mathlib.Data.Fintype.Card

namespace M31FourCoverage.PrivatePivots

/-- The observed deletion cardinality is sufficient to infer exactly one
nonzero entry in the deleted column. -/
theorem private_of_count {I J K : Type*} [Fintype I] [DecidableEq I] [Zero K]
    [DecidableEq K] (v : I → J → K) (j : J)
    (h : Fintype.card I = (Finset.univ.filter (fun i => v i j = 0)).card + 1) :
    ∃! i, v i j ≠ 0 := by
  let kept := Finset.univ.filter (fun i => v i j = 0)
  have hc : (Finset.univ \ kept).card = 1 := by
    rw [Finset.card_sdiff_of_subset (Finset.subset_univ _), Finset.card_univ, h]
    simp [kept]
  simpa [kept] using Finset.card_eq_one_iff_existsUnique.mp hc

end M31FourCoverage.PrivatePivots
