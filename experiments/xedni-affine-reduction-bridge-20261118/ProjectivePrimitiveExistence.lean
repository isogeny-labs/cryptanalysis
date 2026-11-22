import ProjectivePrimitiveUniqueness
import Mathlib.Tactic

/-! Construct a primitive integer representative of a nonzero projective
triple by dividing its coordinates by their common gcd. -/
namespace XedniProjectivePrimitiveExistence

open XedniProjectivePrimitiveUniqueness
open WeierstrassCurve.Projective

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

private def gcd3 (A : Fin 3 → ℤ) : ℕ :=
  Int.gcd ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) (A 2)

private def normalize (A : Fin 3 → ℤ) : Fin 3 → ℤ :=
  fun i => A i / (gcd3 A : ℤ)

private theorem gcd3_pos {A : Fin 3 → ℤ} (hA : A ≠ 0) : 0 < gcd3 A := by
  have hcases : A 0 ≠ 0 ∨ A 1 ≠ 0 ∨ A 2 ≠ 0 := by
    by_contra h
    push Not at h
    obtain ⟨h0, h1, h2⟩ := h
    apply hA
    ext i
    fin_cases i <;> simp [h0, h1, h2]
  rcases hcases with h0 | h1 | h2
  · have hg12 : 0 < Int.gcd (A 0) (A 1) :=
      Int.gcd_pos_of_ne_zero_left (A 1) h0
    have hg12' : ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) ≠ 0 := by
      exact_mod_cast (Nat.ne_of_gt hg12)
    exact Int.gcd_pos_of_ne_zero_left (A 2) hg12'
  · have hg12 : 0 < Int.gcd (A 0) (A 1) :=
      Int.gcd_pos_of_ne_zero_right (A 0) h1
    have hg12' : ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) ≠ 0 := by
      exact_mod_cast (Nat.ne_of_gt hg12)
    exact Int.gcd_pos_of_ne_zero_left (A 2) hg12'
  · exact Int.gcd_pos_of_ne_zero_right
      ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) h2

private theorem gcd3_dvd (A : Fin 3 → ℤ) (i : Fin 3) :
    (gcd3 A : ℤ) ∣ A i := by
  fin_cases i
  · exact dvd_trans
      (Int.gcd_dvd_left ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) (A 2))
      (Int.gcd_dvd_left (A 0) (A 1))
  · exact dvd_trans
      (Int.gcd_dvd_left ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) (A 2))
      (Int.gcd_dvd_right (A 0) (A 1))
  · exact Int.gcd_dvd_right ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) (A 2)

private theorem gcd3_bezout (A : Fin 3 → ℤ) :
    ∃ a b c : ℤ, (gcd3 A : ℤ) = a * A 0 + b * A 1 + c * A 2 := by
  let d : ℕ := Int.gcd (A 0) (A 1)
  let a : ℤ := Int.gcdA (A 0) (A 1) * Int.gcdA (d : ℤ) (A 2)
  let b : ℤ := Int.gcdB (A 0) (A 1) * Int.gcdA (d : ℤ) (A 2)
  let c : ℤ := Int.gcdB (d : ℤ) (A 2)
  refine ⟨a, b, c, ?_⟩
  have h12 := Int.gcd_eq_gcd_ab (A 0) (A 1)
  have h123 := Int.gcd_eq_gcd_ab (d : ℤ) (A 2)
  dsimp [gcd3, a, b, c, d] at *
  linear_combination h123 + Int.gcdA ((Int.gcd (A 0) (A 1) : ℕ) : ℤ) (A 2) * h12

/-- Every nonzero integer projective triple has a primitive integer vector
on the same rational projective class. -/
theorem exists_primitive_int_representative (A : Fin 3 → ℤ) (hA : A ≠ 0) :
    ∃ U : Fin 3 → ℤ, Primitive U ∧ (q ∘ A) ≈ (q ∘ U) := by
  let U := normalize A
  let g := gcd3 A
  have hg : 0 < g := gcd3_pos hA
  have hg0 : (g : ℤ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hg)
  have hfactor (i : Fin 3) : A i = (g : ℤ) * U i := by
    dsimp [U, normalize, g]
    simpa [mul_comm] using (Int.ediv_mul_cancel (gcd3_dvd A i)).symm
  obtain ⟨a, b, c, hbez⟩ := gcd3_bezout A
  have hsum : (g : ℤ) = (g : ℤ) *
      (a * U 0 + b * U 1 + c * U 2) := by
    calc
      (g : ℤ) = a * A 0 + b * A 1 + c * A 2 := hbez
      _ = (g : ℤ) * (a * U 0 + b * U 1 + c * U 2) := by
        rw [hfactor 0, hfactor 1, hfactor 2]
        ring
  have hprim : Primitive U := by
    refine ⟨a, b, c, ?_⟩
    have hcancel : (1 : ℤ) = a * U 0 + b * U 1 + c * U 2 := by
      apply mul_left_cancel₀ hg0
      simpa using hsum
    exact hcancel.symm
  have hvec : A = (g : ℤ) • U := by
    ext i
    exact hfactor i
  have hunit : IsUnit (q (g : ℤ)) := by
    have hgQ : ((g : ℤ) : ℚ) ≠ 0 := by exact_mod_cast hg0
    exact hgQ.isUnit
  refine ⟨U, hprim, ?_⟩
  rw [hvec, WeierstrassCurve.Projective.comp_smul]
  exact WeierstrassCurve.Projective.smul_equiv (q ∘ U) hunit

private def denominatorProduct (P : Fin 3 → ℚ) : ℕ :=
  (P 0).den * (P 1).den * (P 2).den

private def clearDenominators (P : Fin 3 → ℚ) : Fin 3 → ℤ :=
  ![(P 0).num * (P 1).den * (P 2).den,
    (P 0).den * (P 1).num * (P 2).den,
    (P 0).den * (P 1).den * (P 2).num]

private theorem denominatorProduct_ne_zero (P : Fin 3 → ℚ) :
    (denominatorProduct P : ℚ) ≠ 0 := by
  have h0 := (P 0).den_nz
  have h1 := (P 1).den_nz
  have h2 := (P 2).den_nz
  exact_mod_cast (mul_ne_zero (mul_ne_zero h0 h1) h2)

private theorem clearDenominators_coordinate (P : Fin 3 → ℚ)
    (i : Fin 3) :
    ((clearDenominators P i : ℤ) : ℚ) =
      (denominatorProduct P : ℚ) * P i := by
  fin_cases i
  · have hd : ((P 0).den : ℚ) ≠ 0 := by exact_mod_cast (P 0).den_nz
    have hrat := (P 0).num_div_den
    change (((P 0).num * (P 1).den * (P 2).den : ℤ) : ℚ) =
      ((P 0).den * (P 1).den * (P 2).den : ℕ) * P 0
    push_cast
    conv_rhs => arg 2; change P 0; rw [← hrat]
    field_simp [hd]
  · have hd : ((P 1).den : ℚ) ≠ 0 := by exact_mod_cast (P 1).den_nz
    have hrat := (P 1).num_div_den
    change (((P 0).den * (P 1).num * (P 2).den : ℤ) : ℚ) =
      ((P 0).den * (P 1).den * (P 2).den : ℕ) * P 1
    push_cast
    conv_rhs => arg 2; change P 1; rw [← hrat]
    field_simp [hd]
  · have hd : ((P 2).den : ℚ) ≠ 0 := by exact_mod_cast (P 2).den_nz
    have hrat := (P 2).num_div_den
    change (((P 0).den * (P 1).den * (P 2).num : ℤ) : ℚ) =
      ((P 0).den * (P 1).den * (P 2).den : ℕ) * P 2
    push_cast
    conv_rhs => arg 2; change P 2; rw [← hrat]
    field_simp [hd]

/-- Every nonzero rational projective triple has a primitive integral
representative of the same rational projective class. -/
theorem exists_primitive_rational_representative
    (P : Fin 3 → ℚ) (hP : P ≠ 0) :
    ∃ U : Fin 3 → ℤ, Primitive U ∧ P ≈ (q ∘ U) := by
  let A := clearDenominators P
  let D := denominatorProduct P
  have hD : (D : ℚ) ≠ 0 := denominatorProduct_ne_zero P
  have hA : A ≠ 0 := by
    intro hzero
    apply hP
    ext i
    have hi := clearDenominators_coordinate P i
    have hz := congrFun hzero i
    change A i = 0 at hz
    change (A i : ℚ) = (D : ℚ) * P i at hi
    rw [hz] at hi
    have hmul : (D : ℚ) * P i = 0 := by simpa using hi.symm
    simpa using (mul_eq_zero.mp hmul).resolve_left hD
  obtain ⟨U, hprim, hAU⟩ := exists_primitive_int_representative A hA
  have hvec : q ∘ A = (D : ℚ) • P := by
    ext i
    exact clearDenominators_coordinate P i
  have hAP : (q ∘ A) ≈ P := by
    rw [hvec]
    exact WeierstrassCurve.Projective.smul_equiv P hD.isUnit
  exact ⟨U, hprim, Setoid.trans (Setoid.symm hAP) hAU⟩

#print axioms exists_primitive_int_representative
#print axioms exists_primitive_rational_representative

end XedniProjectivePrimitiveExistence
