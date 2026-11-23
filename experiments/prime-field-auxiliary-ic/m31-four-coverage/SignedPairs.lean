import Mathlib.Tactic

namespace M31SignedPairs

/-- For the two affine secant slopes, the single recovered reciprocal
suffices for both full affine outputs. Equal abscissas use a separate path. -/
theorem signed_secants {K : Type*} [Field K] (x y u v pre post carry : K)
    (h : carry * (pre * (u - x) * post) = 1) :
    let r := carry * pre * post
    let finish := fun (s : K) =>
      let a := s^2 - x - u
      (a, s * (x - a) - y)
    (finish ((v-y)*r), finish ((-v-y)*r)) =
      (finish ((v-y)/(u-x)), finish ((-v-y)/(u-x))) := by
  have hr : (carry * pre * post) * (u-x) = 1 := by
    linear_combination h
  have hi : carry * pre * post = (u-x)⁻¹ := (eq_inv_of_mul_eq_one_left hr)
  simp [hi, div_eq_mul_inv]

end M31SignedPairs
