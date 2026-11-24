import MarginalArrival
import Mathlib.Algebra.BigOperators.Group.Finset.Piecewise
import Mathlib.Algebra.Group.Equiv.Defs

namespace M31TranslatedMarginals

variable {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G]

/-- Translating a fixed point by every group element visits a public set
exactly as many times as that set has elements. -/
theorem single (hits : Finset G) (a : G) :
    (∑ h : G, if h + a ∈ hits then 1 else 0 : ℕ) = hits.card := by
  classical
  calc
    _ = ∑ y : G, (if y ∈ hits then 1 else 0 : ℕ) :=
      Equiv.sum_comp (Equiv.addRight a) _
    _ = _ := by simp

/-- Joint hits depend on the displacement between the two fixed slots. -/
theorem joint (hits : Finset G) (a b : G) :
    (∑ h : G, if h + a ∈ hits ∧ h + b ∈ hits then 1 else 0 : ℕ) =
      (hits.filter (fun y => y + (b-a) ∈ hits)).card := by
  convert single (hits.filter (fun y => y + (b-a) ∈ hits)) a using 1
  apply Finset.sum_congr rfl
  intro h _
  simp [add_comm, add_left_comm, add_assoc, sub_eq_add_neg]

theorem success_bound {Q : Type*} (slots : Finset Q) (path : Q → G)
    (hits : Finset G) (success : G → Bool) (k : ℕ)
    (necessary : ∀ h, success h = true →
      k ≤ ∑ q ∈ slots, if h + path q ∈ hits then 1 else 0) :
    (Finset.univ.filter (fun h => success h)).card * k ≤ slots.card * hits.card := by
  exact M31MarginalArrival.count_bound Finset.univ slots
    (fun h q => if h + path q ∈ hits then 1 else 0) success k hits.card
    (fun h _ => necessary h) (fun q _ => single hits (path q))

end M31TranslatedMarginals
