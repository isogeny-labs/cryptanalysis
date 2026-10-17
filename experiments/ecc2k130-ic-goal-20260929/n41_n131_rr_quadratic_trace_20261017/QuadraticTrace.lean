import Std
import Init.Grind.Ring.Basic

namespace QuadraticTrace
open Lean.Grind

/-- A shared quadratic trace certificate excludes a zero determinant in every
signed chart covered by the certificate. The coefficient and trace equations
that produce the certificate are separate finite computations. -/
theorem separator_excludes_zero {F S : Type} [CommSemiring F]
    (trace : F → Bool) (trace_zero : trace 0 = false)
    (a b : F) (det : S → F)
    (certificate : ∀ s, trace (a * det s + b * ((det s * det s) * det s)) = true) :
    ∀ s, det s ≠ 0 := by
  intro s hzero
  have h := certificate s
  simp [hzero, Semiring.mul_zero,
        Semiring.add_zero, trace_zero] at h

/-- A witnessed zero blocks every shared certificate of the stated form. -/
theorem witnessed_zero_blocks_separator {F S : Type} [CommSemiring F]
    (trace : F → Bool) (trace_zero : trace 0 = false)
    (det : S → F) (witness : S) (zero_det : det witness = 0) :
    ¬ ∃ a b : F, ∀ s, trace (a * det s + b * ((det s * det s) * det s)) = true := by
  rintro ⟨a, b, certificate⟩
  exact (separator_excludes_zero trace trace_zero a b det certificate witness) zero_det

#print axioms separator_excludes_zero
#print axioms witnessed_zero_blocks_separator

end QuadraticTrace
