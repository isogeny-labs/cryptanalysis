import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31.TwistQuotients

variable {F : Type*} [Field F] [Fintype F] [DecidableEq F]

private theorem square_sum (hF : ringChar F ≠ 2) (f : F → ℤ) :
    ∑ x : F, f (x^2) = ∑ u : F, (quadraticChar F u + 1) * f u := by
  classical
  calc
    _ = ∑ x : F, ∑ u : F, if x^2 = u then f u else 0 := by simp
    _ = ∑ u : F, ∑ x : F, if x^2 = u then f u else 0 := Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro u _
      rw [← quadraticChar_card_sqrts hF u, ← Finset.sum_filter]
      simp [Set.toFinset_setOf]

private def cubic (a b u : F) := u^3 + 2*a*u^2 + a^2*u - b^2
private def reciprocal (a b v : F) := 1 + 2*a*v + a^2*v^2 - b^2*v^3

private theorem swap (a b u : F) :
    quadraticChar F u * quadraticChar F (cubic a b u) =
    quadraticChar F (reciprocal a b u⁻¹) - (if u = 0 then 1 else 0) := by
  by_cases hu : u = 0
  · simp [hu, reciprocal]
  · have h : u * cubic a b u = (u^2)^2 * reciprocal a b u⁻¹ := by
      unfold cubic reciprocal
      field_simp
    rw [← map_mul, h, map_mul, quadraticChar_sq_one' (pow_ne_zero 2 hu)]
    simp [hu]

/-- Character correlation for the two cubics x³ + ax ± b, in odd characteristic. -/
theorem family_correlation (a b : F) (hF : ringChar F ≠ 2) :
    ∑ x : F, quadraticChar F ((x^3 + a*x + b)*(x^3 + a*x - b)) =
      (∑ u : F, quadraticChar F (u^3 + 2*a*u^2 + a^2*u - b^2)) +
      (∑ v : F, quadraticChar F (1 + 2*a*v + a^2*v^2 - b^2*v^3)) - 1 := by
  classical
  have h (x : F) : (x^3+a*x+b)*(x^3+a*x-b) = cubic a b (x^2) := by unfold cubic; ring
  simp_rw [h]
  rw [square_sum hF (fun u => quadraticChar F (cubic a b u))]
  simp_rw [add_mul, one_mul, swap]
  rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  have invsum := Equiv.sum_comp (Equiv.inv F) (fun v => quadraticChar F (reciprocal a b v))
  change (∑ v : F, quadraticChar F (reciprocal a b v⁻¹)) = _ at invsum
  rw [invsum]
  simp [reciprocal, cubic]
  ring

/-- Character correlation for the two cubics x³ + 2x ± 14, in odd characteristic. -/
theorem correlation (hF : ringChar F ≠ 2) :
    ∑ x : F, quadraticChar F ((x^3 + 2*x + 14)*(x^3 + 2*x - 14)) =
      (∑ u : F, quadraticChar F (u^3 + 4*u^2 + 4*u - 196)) +
      (∑ v : F, quadraticChar F (1 + 4*v + 4*v^2 - 196*v^3)) - 1 := by
  convert family_correlation (2 : F) 14 hF using 1
  norm_num

/-- One point at infinity together with the affine pairs satisfying y² = f(x). -/
abbrev CurvePoints (f : F → F) := Option ((x : F) × {y : F // y^2 = f x})

def pointTrace (f : F → F) : ℤ :=
  (Fintype.card F : ℤ) + 1 - Fintype.card (CurvePoints f)

theorem trace_eq (hF : ringChar F ≠ 2) (f : F → F) :
    pointTrace f = -(∑ x : F, quadraticChar F (f x)) := by
  classical
  have fiber (x : F) : (Fintype.card {y : F // y^2 = f x} : ℤ) =
      quadraticChar F (f x) + 1 := by
    simpa [Fintype.card_subtype, Set.toFinset_setOf] using quadraticChar_card_sqrts hF (f x)
  simp only [pointTrace, CurvePoints, Fintype.card_option, Fintype.card_sigma,
    Nat.cast_add, Nat.cast_one, Nat.cast_sum, fiber, Finset.sum_add_distrib]
  simp

private theorem monic_sum (a b c d : F) (ha : a ≠ 0) :
    (∑ x : F, quadraticChar F (a*x^3+b*x^2+c*x+d)) =
      ∑ X : F, quadraticChar F (X^3+b*X^2+a*c*X+a^2*d) := by
  have eqn (x : F) : (a*x)^3+b*(a*x)^2+a*c*(a*x)+a^2*d =
      a^2*(a*x^3+b*x^2+c*x+d) := by ring
  have reindex := Equiv.sum_comp (Equiv.mulLeft₀ a ha)
    (fun X => quadraticChar F (X^3+b*X^2+a*c*X+a^2*d))
  change (∑ x : F, quadraticChar F ((a*x)^3+b*(a*x)^2+a*c*(a*x)+a^2*d)) = _ at reindex
  simpa only [eqn, map_mul, quadraticChar_sq_one' ha, one_mul] using reindex

/-- The point counts on precisely the two monic models used in the GP replay
determine the original correlation. The second change of variables needs 196 ≠ 0. -/
theorem correlation_traces (hF : ringChar F ≠ 2) (ha : (-196 : F) ≠ 0) :
    ∑ x : F, quadraticChar F ((x^3 + 2*x + 14)*(x^3 + 2*x - 14)) =
      -1 - pointTrace (fun u : F => u^3 + 4*u^2 + 4*u - 196)
         - pointTrace (fun u : F => u^3 + 4*u^2 - 784*u + 196^2) := by
  rw [correlation hF, trace_eq hF, trace_eq hF]
  have h := monic_sum (-196 : F) 4 4 1 ha
  have hm : (∑ v : F, quadraticChar F (1 + 4*v + 4*v^2 - 196*v^3)) =
      ∑ v : F, quadraticChar F (v^3 + 4*v^2 - 784*v + 196^2) := by
    convert h using 2 <;> congr 1 <;> ring
  rw [hm]
  ring

/-- Four times the number of common liftable abscissae, with both marginal
traces charged and the correlation evaluated on the same field. -/
theorem four_common (hF : ringChar F ≠ 2) (f g : F → F)
    (hf : ∀ x, f x ≠ 0) (hg : ∀ x, g x ≠ 0)
    [DecidablePred (fun x => IsSquare (f x) ∧ IsSquare (g x))] :
    4 * (Fintype.card {x // IsSquare (f x) ∧ IsSquare (g x)} : ℤ) =
      Fintype.card F - pointTrace f - pointTrace g +
        ∑ x : F, quadraticChar F (f x * g x) := by
  classical
  have row (x : F) :
      (if IsSquare (f x) ∧ IsSquare (g x) then (4 : ℤ) else 0) =
      1 + quadraticChar F (f x) + quadraticChar F (g x) + quadraticChar F (f x*g x) := by
    simp only [map_mul, ← quadraticChar_one_iff_isSquare (hf x),
      ← quadraticChar_one_iff_isSquare (hg x)]
    rcases quadraticChar_dichotomy (hf x) with h | h <;>
      rcases quadraticChar_dichotomy (hg x) with k | k <;> simp [h,k]
  have allRows := Finset.sum_congr (s₁ := Finset.univ) rfl (fun x _ => row x)
  rw [← Finset.sum_filter] at allRows
  simp only [Finset.sum_const, nsmul_eq_mul, Finset.sum_add_distrib, Finset.card_univ,
    mul_one] at allRows
  rw [Fintype.card_subtype, trace_eq hF, trace_eq hF]
  linarith

end M31.TwistQuotients
