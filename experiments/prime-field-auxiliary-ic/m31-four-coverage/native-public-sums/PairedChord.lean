import Mathlib.Tactic

namespace M31.PairedChord

variable {F : Type*} [Field F]

/-- The backward product in a batch inversion recovers the inverse of the
current denominator. The prefix and suffix represent the other factors. -/
theorem batch_inverse (pre delta suffix : F)
    (hp : pre ≠ 0) (hd : delta ≠ 0) (hs : suffix ≠ 0) :
    pre * (pre * delta * suffix)⁻¹ * suffix = delta⁻¹ := by
  field_simp

/-- Negation of the right point changes only the numerator. Both downstream
coordinate formulas can consume these slopes with the same two abscissae. -/
theorem signed_slopes (x y u v : F) :
    ((y-v) * (x-u)⁻¹, (y+v) * (x-u)⁻¹) =
    ((y-v)/(x-u), (y-(-v))/(x-u)) := by
  simp [div_eq_mul_inv]

end M31.PairedChord
