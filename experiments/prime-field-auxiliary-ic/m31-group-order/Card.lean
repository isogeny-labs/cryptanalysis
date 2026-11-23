import Mathlib
/-!
Point-order certificate for the base point in
`experiments/prime-field-auxiliary-ic/snapshot/comparison/field31/auxiliary/public.json`.
The unconditional certificates below use a two-point fiber bound and a prime-order witness.
-/
namespace M31Card

abbrev F := ZMod 2147483647

instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def E : WeierstrassCurve.Affine F := ⟨0, 0, 0, 2, 14⟩

def P : E.Point := .some (x := 1) (y := 814455902) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

def atInfinity {W : WeierstrassCurve.Affine F} : W.Point → Bool
  | .zero => true
  | .some _ _ _ => false

private theorem zero_of_infinity {W : WeierstrassCurve.Affine F} (A : W.Point)
    (h : atInfinity A = true) : A = 0 := by
  cases A with
  | zero => rfl
  | some x y cert => contradiction

theorem multiple : (2147505293 : ℕ) • P = 0 := by
  apply zero_of_infinity
  native_decide

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

section FiberBound
variable {K : Type*} [Field K] [Fintype K]

private def abscissa {W : WeierstrassCurve.Affine K} : W.Point → Option K
  | .zero => none
  | .some x _ _ => some x

omit [Fintype K] in
private theorem sameAbscissa {W : WeierstrassCurve.Affine K} (A B : W.Point)
    (h : abscissa A = abscissa B) : A = B ∨ A = -B := by
  apply WeierstrassCurve.Affine.Point.xRep_eq_xRep_iff.mp
  cases A <;> cases B <;> simp_all [abscissa]

/-- Two signs and an optional x-coordinate suffice to cover every point. -/
theorem cardBounds (W : WeierstrassCurve.Affine K) :
    0 < Nat.card W.Point ∧ Nat.card W.Point ≤ 2*(Fintype.card K+1) := by
  classical
  let pick : Option K → W.Point := Function.invFun abscissa
  let decode : Option K × Bool → W.Point := fun z =>
    if z.2 then -(pick z.1) else pick z.1
  have surj : Function.Surjective decode := by
    intro A
    have h : abscissa (pick (abscissa A)) = abscissa A :=
      Function.invFun_eq ⟨A, rfl⟩
    rcases sameAbscissa A _ h.symm with e | e
    · exact ⟨(abscissa A, false), e.symm⟩
    · exact ⟨(abscissa A, true), e.symm⟩
  let : Finite W.Point := Finite.of_surjective decode surj
  refine ⟨Nat.card_pos, ?_⟩
  have h := Nat.card_le_card_of_surjective decode surj
  simpa [Nat.card_eq_fintype_card, Nat.mul_comm] using h

end FiberBound

theorem firstCardinality : Nat.card E.Point = 2147505293 := by
  obtain ⟨hpos, hmax⟩ := cardBounds E
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at hmax
  have hd := addOrderOf_dvd_natCard P
  rw [order] at hd
  omega

def secondCurve : WeierstrassCurve.Affine F := ⟨0, 0, 0, 2, 36⟩

def secondPoint : secondCurve.Point := .some (x := 0) (y := 6) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

theorem secondPointOrder : addOrderOf secondPoint = 2147506201 := by
  have vanishes : (2147506201 : ℕ) • secondPoint = 0 := by
    apply zero_of_infinity
    native_decide
  rcases (Nat.dvd_prime (by native_decide : Nat.Prime 2147506201)).mp
    (addOrderOf_dvd_of_nsmul_eq_zero vanishes) with h | h
  · exact (WeierstrassCurve.Affine.Point.some_ne_zero _
      (AddMonoid.addOrderOf_eq_one_iff.mp h)).elim
  · exact h

theorem secondCardinality : Nat.card secondCurve.Point = 2147506201 := by
  obtain ⟨hpos, hmax⟩ := cardBounds secondCurve
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at hmax
  have hd := addOrderOf_dvd_natCard secondPoint
  rw [secondPointOrder] at hd
  omega

end M31Card
