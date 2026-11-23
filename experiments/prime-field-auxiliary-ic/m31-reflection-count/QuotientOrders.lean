import Mathlib

namespace M31Reflection

abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def leftCurve : WeierstrassCurve.Affine F := ⟨0, -4, 0, 4, 196⟩
def rightCurve : WeierstrassCurve.Affine F := ⟨0, -4, 0, -784, -38416⟩

theorem smooth : leftCurve.Δ ≠ 0 ∧ rightCurve.Δ ≠ 0 := by native_decide

def leftPoint : leftCurve.Point := .some (x := 3) (y := 1498289385) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

def rightPoint : rightCurve.Point := .some (x := 2) (y := 221281234) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

private def infinity {E : WeierstrassCurve.Affine F} (q : E.Point) : Bool := by
  cases q
  · exact true
  · exact false

private theorem zero_of_infinity {E : WeierstrassCurve.Affine F} (q : E.Point)
    (h : infinity q = true) : q = 0 := by
  cases q <;> first | rfl | simp_all [infinity]

private theorem nonzero_of_finite {E : WeierstrassCurve.Affine F} (q : E.Point)
    (h : infinity q = false) : q ≠ 0 := by
  intro eq
  subst q
  cases h

theorem left_order : addOrderOf leftPoint = 2147552589 := by
  apply addOrderOf_eq_of_nsmul_and_div_prime_nsmul (by decide)
  · apply zero_of_infinity
    native_decide
  · intro q prime divides
    have mem := (Nat.mem_primeFactors.mpr ⟨prime, divides, by decide⟩)
    have factors : Nat.primeFactors 2147552589 = {3, 7, 13, 7866493} := by native_decide
    rw [factors] at mem
    simp only [Finset.mem_insert, Finset.mem_singleton] at mem
    rcases mem with rfl | rfl | rfl | rfl <;>
      apply nonzero_of_finite <;> native_decide

theorem right_order : addOrderOf rightPoint = 2147520649 := by
  apply addOrderOf_eq_of_nsmul_and_div_prime_nsmul (by decide)
  · apply zero_of_infinity
    native_decide
  · intro q prime divides
    have mem := (Nat.mem_primeFactors.mpr ⟨prime, divides, by decide⟩)
    have factors : Nat.primeFactors 2147520649 = {23, 67, 1393589} := by native_decide
    rw [factors] at mem
    simp only [Finset.mem_insert, Finset.mem_singleton] at mem
    rcases mem with rfl | rfl | rfl <;>
      apply nonzero_of_finite <;> native_decide

private def encode {E : WeierstrassCurve.Affine F} : E.Point → Option (F × Bool)
  | .zero => none
  | .some x y _ => some (x, decide (y.val ≤ (-y).val))

private theorem encode_inj (E : WeierstrassCurve.Affine F) (h₁ : E.a₁ = 0)
    (h₃ : E.a₃ = 0) : Function.Injective (encode (E := E)) := by
  intro a b eq
  cases a with
  | zero => cases b <;> simp_all [encode]
  | some x y hy =>
    cases b with
    | zero => simp [encode] at eq
    | some u v hv =>
      simp only [encode, Option.some.injEq, Prod.mk.injEq] at eq
      obtain ⟨rfl, bits⟩ := eq
      have hy' := (E.equation_iff _ _).mp ((E.nonsingular_iff _ _).mp hy).1
      have hv' := (E.equation_iff _ _).mp ((E.nonsingular_iff _ _).mp hv).1
      simp only [h₁, h₃, zero_mul, add_zero] at hy' hv'
      rcases (sq_eq_sq_iff_eq_or_eq_neg.mp (hy'.trans hv'.symm)) with rfl | neg
      · rfl
      · subst y
        change decide ((-v).val ≤ (- -v).val) = decide (v.val ≤ (-v).val) at bits
        have invol := congrArg (fun t : F => decide ((-v).val ≤ t.val)) (neg_neg v)
        have flip : decide ((-v).val ≤ v.val) = decide (v.val ≤ (-v).val) :=
          invol.symm.trans bits
        simp only [decide_eq_decide] at flip
        have same : (-v).val = v.val := by omega
        have eqv := ZMod.val_injective 2147483647 same
        congr

private theorem code_card (q : ℕ) [NeZero q] :
    Nat.card (Option (ZMod q × Bool)) = q * 2 + 1 := by
  simp [Nat.card_eq_fintype_card, Fintype.card_option, Fintype.card_prod, ZMod.card]

private theorem size (E : WeierstrassCurve.Affine F) (h₁ : E.a₁ = 0)
    (h₃ : E.a₃ = 0) (n : ℕ) (large : 2147483647 < n) (hd : n ∣ Nat.card E.Point) :
    Nat.card E.Point = n := by
  have inj := encode_inj E h₁ h₃
  let : Finite E.Point := Finite.of_injective _ inj
  have pos := Nat.card_pos (α := E.Point)
  have bound := Nat.card_le_card_of_injective _ inj
  rw [code_card] at bound
  obtain ⟨k, hk⟩ := hd
  rcases k with _ | ⟨_ | k⟩
  · simp only [Nat.mul_zero] at hk
    omega
  · simpa using hk
  · rw [hk, Nat.mul_succ, Nat.mul_succ] at bound
    omega

theorem quotient_cardinalities :
    Nat.card leftCurve.Point = 2147552589 ∧ Nat.card rightCurve.Point = 2147520649 := by
  constructor
  · apply size leftCurve rfl rfl _ (by decide)
    rw [← left_order]
    exact addOrderOf_dvd_natCard leftPoint
  · apply size rightCurve rfl rfl _ (by decide)
    rw [← right_order]
    exact addOrderOf_dvd_natCard rightPoint

end M31Reflection
