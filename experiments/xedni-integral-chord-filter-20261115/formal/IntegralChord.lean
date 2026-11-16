import Mathlib

namespace XedniIntegralChord

/-- The two point equations and the tangent equation force the monic slope relation. -/
theorem monic_relation_of_tangent
    (x₁ y₁ x₂ y₂ a₁ a₂ a₃ a₄ a₆ m : ℚ)
    (hx : x₁ ≠ x₂)
    (hm : m * (x₁ - x₂) = y₁ - y₂)
    (hU : y₁ ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ -
      x₁ ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆ = 0)
    (hV : y₂ ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ -
      x₂ ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆ = 0)
    (htan : m * (2 * y₂ + a₁ * x₂ + a₃) -
      (3 * x₂ ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂) = 0) :
    m ^ 2 + a₁ * m = a₂ + x₁ + 2 * x₂ := by
  have hy : y₁ = y₂ + m * (x₁ - x₂) := by linarith [hm]
  have hid : (x₁ - x₂) ^ 2 * (m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂) =
      (y₁ ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ - x₁ ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆) -
      (y₂ ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ - x₂ ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆) -
      (x₁ - x₂) * (m * (2 * y₂ + a₁ * x₂ + a₃) -
        (3 * x₂ ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂)) := by
    rw [hy]
    ring
  have hz : (x₁ - x₂) ^ 2 * (m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂) = 0 := by
    rw [hid, hU, hV, htan]
    ring
  have hd : (x₁ - x₂) ^ 2 ≠ 0 := pow_ne_zero 2 (sub_ne_zero.mpr hx)
  have hr : m ^ 2 + a₁ * m - a₂ - x₁ - 2 * x₂ = 0 :=
    (mul_eq_zero.mp hz).resolve_left hd
  linarith

/-- A rational chord slope satisfying the integral monic relation is integral. -/
theorem integer_slope_of_monic_relation (m : ℚ) (a b : ℤ)
    (h : m ^ 2 + (a : ℚ) * m = (b : ℚ)) :
    ∃ z : ℤ, (z : ℚ) = m := by
  let f : Polynomial ℤ := Polynomial.X ^ 2 + (Polynomial.C a * Polynomial.X - Polynomial.C b)
  have hlinear : (Polynomial.C a * Polynomial.X).degree ≤ 1 := by
    simpa [pow_one] using (Polynomial.degree_C_mul_X_pow_le 1 a)
  have hdeg : (Polynomial.C a * Polynomial.X - Polynomial.C b).degree < 2 := by
    exact (Polynomial.degree_sub_le _ _).trans_lt
      ((max_le hlinear (Polynomial.degree_C_le.trans (by norm_num))).trans_lt
        (by norm_num))
  have hmonic : f.Monic := by
    change (Polynomial.X ^ 2 +
      (Polynomial.C a * Polynomial.X - Polynomial.C b)).Monic
    exact Polynomial.monic_X_pow_add hdeg
  have hroot : Polynomial.aeval m f = 0 := by
    simp [f]
    linarith [h]
  exact (IsIntegrallyClosed.isIntegral_iff.mp ⟨f, hmonic, hroot⟩)

/-- The algebraic tangent bridge plus integral first coefficients and x coordinates. -/
theorem integer_slope_of_tangent
    (x₁ y₁ x₂ y₂ a₁ a₂ : ℤ) (a₃ a₄ a₆ m : ℚ)
    (hx : x₁ ≠ x₂)
    (hm : m * ((x₁ : ℚ) - x₂) = (y₁ : ℚ) - y₂)
    (hU : (y₁ : ℚ) ^ 2 + a₁ * x₁ * y₁ + a₃ * y₁ -
      (x₁ : ℚ) ^ 3 - a₂ * x₁ ^ 2 - a₄ * x₁ - a₆ = 0)
    (hV : (y₂ : ℚ) ^ 2 + a₁ * x₂ * y₂ + a₃ * y₂ -
      (x₂ : ℚ) ^ 3 - a₂ * x₂ ^ 2 - a₄ * x₂ - a₆ = 0)
    (htan : m * (2 * (y₂ : ℚ) + a₁ * x₂ + a₃) -
      (3 * (x₂ : ℚ) ^ 2 + 2 * a₂ * x₂ + a₄ - a₁ * y₂) = 0) :
    ∃ z : ℤ, (z : ℚ) = m := by
  have hxc : (x₁ : ℚ) ≠ x₂ := by exact_mod_cast hx
  have hquad := monic_relation_of_tangent
    (x₁ : ℚ) y₁ x₂ y₂ a₁ a₂ a₃ a₄ a₆ m hxc hm hU hV htan
  exact integer_slope_of_monic_relation m a₁ (a₂ + x₁ + 2 * x₂)
    (by exact_mod_cast hquad)

/-- The affine group relation itself yields the monic slope equation. -/
theorem monic_relation_of_group_relation
    (W : WeierstrassCurve.Affine ℚ) [W.IsElliptic]
    (x₁ y₁ x₂ y₂ : ℚ)
    (h₁ : W.Nonsingular x₁ y₁) (h₂ : W.Nonsingular x₂ y₂)
    (hx : x₁ ≠ x₂)
    (hrel : WeierstrassCurve.Affine.Point.some x₁ y₁ h₁ + WeierstrassCurve.Affine.Point.some x₂ y₂ h₂ +
      WeierstrassCurve.Affine.Point.some x₂ y₂ h₂ = 0) :
    let m := (y₁ - y₂) / (x₁ - x₂)
    m ^ 2 + W.a₁ * m = W.a₂ + x₁ + 2 * x₂ := by
  let U : W.Point := WeierstrassCurve.Affine.Point.some x₁ y₁ h₁
  let V : W.Point := WeierstrassCurve.Affine.Point.some x₂ y₂ h₂
  have hdouble : V + V = -U := by
    apply eq_neg_of_add_eq_zero_left
    simpa only [U, V, add_assoc, add_comm, add_left_comm] using hrel
  have hne : y₂ ≠ W.negY x₂ y₂ := by
    intro heq
    have hz := WeierstrassCurve.Affine.Point.add_self_of_Y_eq (h₁ := h₂) heq
    rw [hz] at hdouble
    exact WeierstrassCurve.Affine.Point.some_ne_zero h₁ (neg_eq_zero.mp hdouble.symm)
  have hformula := WeierstrassCurve.Affine.Point.add_self_of_Y_ne' (h₁ := h₂) hne
  have hpoint := neg_injective (hformula.symm.trans hdouble)
  have hxcoord := (WeierstrassCurve.Affine.Point.some.inj hpoint).1
  have hycoord := (WeierstrassCurve.Affine.Point.some.inj hpoint).2
  let lam := W.slope x₂ x₂ y₂ y₂
  have hchord : y₁ - y₂ = lam * (x₁ - x₂) := by
    change W.negAddY x₂ x₂ y₂ lam = y₁ at hycoord
    change W.addX x₂ x₂ lam = x₁ at hxcoord
    change lam * (W.addX x₂ x₂ lam - x₂) + y₂ = y₁ at hycoord
    rw [hxcoord] at hycoord
    linarith [hycoord]
  have hm : (y₁ - y₂) / (x₁ - x₂) = lam := by
    apply (div_eq_iff (sub_ne_zero.mpr hx)).2
    rw [hchord]
  have hquad : lam ^ 2 + W.a₁ * lam = W.a₂ + x₁ + 2 * x₂ := by
    change W.addX x₂ x₂ lam = x₁ at hxcoord
    change lam ^ 2 + W.a₁ * lam - W.a₂ - x₂ - x₂ = x₁ at hxcoord
    linarith [hxcoord]
  simpa [hm] using hquad

/-- A two-point relation on the elliptic-curve group forces an integral chord slope
when the first two curve coefficients and both x coordinates are integral. -/
theorem integer_slope_of_group_relation
    (W : WeierstrassCurve.Affine ℚ) [W.IsElliptic]
    (x₁ y₁ x₂ y₂ : ℚ)
    (h₁ : W.Nonsingular x₁ y₁) (h₂ : W.Nonsingular x₂ y₂)
    (hx : x₁ ≠ x₂)
    (hrel : WeierstrassCurve.Affine.Point.some x₁ y₁ h₁ +
      WeierstrassCurve.Affine.Point.some x₂ y₂ h₂ +
      WeierstrassCurve.Affine.Point.some x₂ y₂ h₂ = 0)
    (ha₁ : ∃ a : ℤ, (a : ℚ) = W.a₁)
    (ha₂ : ∃ a : ℤ, (a : ℚ) = W.a₂)
    (hx₁ : ∃ x : ℤ, (x : ℚ) = x₁)
    (hx₂ : ∃ x : ℤ, (x : ℚ) = x₂) :
    ∃ z : ℤ, (z : ℚ) = (y₁ - y₂) / (x₁ - x₂) := by
  obtain ⟨a₁, ha₁⟩ := ha₁
  obtain ⟨a₂, ha₂⟩ := ha₂
  obtain ⟨n₁, hn₁⟩ := hx₁
  obtain ⟨n₂, hn₂⟩ := hx₂
  let m : ℚ := (y₁ - y₂) / (x₁ - x₂)
  have hquad := monic_relation_of_group_relation W x₁ y₁ x₂ y₂ h₁ h₂ hx hrel
  change m ^ 2 + W.a₁ * m = W.a₂ + x₁ + 2 * x₂ at hquad
  have hcast : m ^ 2 + (a₁ : ℚ) * m = ((a₂ + n₁ + 2 * n₂ : ℤ) : ℚ) := by
    push_cast
    rw [ha₁, ha₂, hn₁, hn₂]
    exact hquad
  simpa only [m] using integer_slope_of_monic_relation m a₁
    (a₂ + n₁ + 2 * n₂) hcast

#print axioms monic_relation_of_tangent
#print axioms integer_slope_of_monic_relation
#print axioms integer_slope_of_tangent
#print axioms monic_relation_of_group_relation
#print axioms integer_slope_of_group_relation

end XedniIntegralChord
