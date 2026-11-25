import Mathlib

namespace M31FourCoverage.PairInversion

/-- Both signs of an affine neighbor use the same reciprocal off the diagonal. -/
theorem slopes {K : Type*} [Field K] (x y u v : K) :
    let r := (u - x)⁻¹
    ((v - y) * r, (-v - y) * r) = ((v - y) / (u - x), (-v - y) / (u - x)) := by
  simp [div_eq_mul_inv]

/-- One reverse step recovers the reciprocal of the final factor and
the inverse prefix needed by the next step. This applies both to a
product inside a lane and to the product of the lane totals. -/
theorem reverse_step {K : Type*} [Field K] {a b : K} (ha : a ≠ 0) (hb : b ≠ 0) :
    (a * (a*b)⁻¹, b * (a*b)⁻¹) = (b⁻¹, a⁻¹) := by
  apply Prod.ext <;> dsimp <;> field_simp

/-- Unequal lane lengths and exceptional (zero) denominators preserve
the single product to be inverted. Empty lanes contribute one. -/
theorem striped_product {K : Type*} [Field K] [DecidableEq K]
    (n : ℕ) (den : Fin n → K) (lane : Fin n → Fin 4) :
    (∏ j : Fin 4, ∏ i : Fin n with lane i = j, (if den i = 0 then 1 else den i)) =
      ∏ i : Fin n, (if den i = 0 then 1 else den i) := by
  exact Finset.prod_fiberwise Finset.univ lane _

/-- A nonzero tangent ordinate can use the same reverse-product step as a secant. -/
theorem tangent_slot {K : Type*} [Field K] [NeZero (2 : K)] (x y a : K) (hy : y ≠ 0) :
    y+y ≠ 0 ∧ (3*x^2+a)*(y+y)⁻¹ = (3*x^2+a)/(2*y) := by
  rw [← two_mul]
  exact ⟨mul_ne_zero (NeZero.ne _) hy, (div_eq_mul_inv _ _).symm⟩

private def extend {M : Type*} [Monoid M] (u : M) (k : ℕ) := u^(2^k) * u

/-- Exponent of the seven-block Mersenne addition chain, including the
last two squarings and the final multiplication by the input. -/
theorem chain_exponent {M : Type*} [Monoid M] (x : M) :
    let a := extend x 1
    let b := a^2*x
    let c := extend b 3
    let d := c^2*x
    let e := extend d 7
    let f := extend e 14
    let g := f^2*x
    g^4*x = x^2147483645 := by
  dsimp only [extend]
  simp only [← pow_succ, ← pow_mul, ← pow_add]
  rfl

end M31FourCoverage.PairInversion
