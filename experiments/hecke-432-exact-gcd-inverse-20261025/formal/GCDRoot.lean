import Std

namespace ExactGCDInverse

universe u v
variable {α : Type u} {β : Type v}

/-- A common-factor polynomial with both divisibility witnesses and a
Bézout identity has exactly the common zeros of the two inputs. The
polynomials are represented by their evaluation functions; the concrete
finite-field gcd computations supply these identities separately. -/
theorem common_root_iff_gcd_root
    [Zero β] [Add β] [Mul β]
    (zero_add_zero : (0 : β) + 0 = 0)
    (mul_zero : ∀ z : β, z * 0 = 0)
    (zero_mul : ∀ z : β, 0 * z = 0)
    (P F g a b u v : α → β)
    (hP : ∀ x, P x = g x * a x)
    (hF : ∀ x, F x = g x * b x)
    (hBezout : ∀ x, g x = u x * P x + v x * F x)
    (x : α) :
    (P x = 0 ∧ F x = 0) ↔ g x = 0 := by
  constructor
  · intro h
    rw [hBezout x, h.1, h.2]
    rw [mul_zero, mul_zero, zero_add_zero]
  · intro h
    constructor
    · rw [hP x, h]
      exact zero_mul _
    · rw [hF x, h]
      exact zero_mul _

#print axioms common_root_iff_gcd_root

end ExactGCDInverse
