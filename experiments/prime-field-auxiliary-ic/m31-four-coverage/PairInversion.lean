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
