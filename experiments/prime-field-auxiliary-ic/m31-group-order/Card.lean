import Mathlib
/-!
Point-order certificate for the base point in
`experiments/prime-field-auxiliary-ic/snapshot/comparison/field31/auxiliary/public.json`.
The final theorem takes the two numerical bounds from Hasse's theorem as hypotheses.
-/
namespace M31Card

abbrev F := ZMod 2147483647

instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def E : WeierstrassCurve.Affine F := ⟨0, 0, 0, 2, 14⟩

def P : E.Point := .some (x := 1) (y := 814455902) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

def atInfinity : E.Point → Bool
  | .zero => true
  | .some _ => false

theorem multiple : (2147505293 : ℕ) • P = 0 := by
  have h : atInfinity ((2147505293 : ℕ) • P) = true := by native_decide
  cases hq : (2147505293 : ℕ) • P <;> first | rfl | simp_all [atInfinity]

theorem order : addOrderOf P = 2147505293 := by
  have d := addOrderOf_dvd_of_nsmul_eq_zero multiple
  rcases (Nat.dvd_prime (by native_decide : Nat.Prime 2147505293)).mp d with h | h
  · have hn : P ≠ 0 := WeierstrassCurve.Affine.Point.some_ne_zero _
    exact (hn (AddMonoid.addOrderOf_eq_one_iff.mp h)).elim
  · exact h

theorem unique_cardinality_in_hasse_interval (N : ℕ) (lower : 2147390967 ≤ N) (upper : N ≤ 2147576329)
    (hd : 2147505293 ∣ N) : N = 2147505293 := by omega

theorem curve_cardinality_of_hasse_bounds
    (lower : 2147390967 ≤ Nat.card E.Point) (upper : Nat.card E.Point ≤ 2147576329) :
    Nat.card E.Point = 2147505293 := by
  apply unique_cardinality_in_hasse_interval _ lower upper
  rw [← order]
  exact addOrderOf_dvd_natCard P

end M31Card
