import Std
import Init.Grind.Ring.Field

namespace InverseTraceANF
open Lean.Grind

theorem first_source_inverse_identity {F : Type} [Field F]
    (a s : F) (ha : a ≠ 0) :
    a * (a * (a + s))⁻¹ = (a + s)⁻¹ := by
  rw [Field.inv_mul, ← Semiring.mul_assoc, Field.mul_inv_cancel ha,
      Semiring.one_mul]

theorem second_source_inverse_identity {F : Type} [Field F]
    (a s : F) (ha : a ≠ 0) (hb : a + s ≠ 0)
    (hchar : ∀ x : F, x + x = 0) :
    s * (a * (a + s))⁻¹ = a⁻¹ + (a + s)⁻¹ := by
  have hs : s = a + (a + s) := by
    rw [← AddCommMonoid.add_assoc, hchar a, AddCommMonoid.zero_add]
  have hfirst : a * (a⁻¹ * (a + s)⁻¹) = (a + s)⁻¹ := by
    rw [← Semiring.mul_assoc, Field.mul_inv_cancel ha, Semiring.one_mul]
  have hsecond : (a + s) * (a⁻¹ * (a + s)⁻¹) = a⁻¹ := by
    rw [CommSemiring.mul_comm a⁻¹, ← Semiring.mul_assoc,
        Field.mul_inv_cancel hb, Semiring.one_mul]
  calc
    s * (a * (a + s))⁻¹ = (a + (a + s)) * (a * (a + s))⁻¹ := by
      congr 1
    _ = a⁻¹ + (a + s)⁻¹ := by
      rw [Field.inv_mul, Semiring.right_distrib, hfirst, hsecond,
          AddCommMonoid.add_comm]

/-- The two inverse-trace source checks equal the product-inverse witness
checks when trace is additive over the binary field. -/
theorem source_trace_conditions_iff {F : Type} [Field F]
    (a s : F) (ha : a ≠ 0) (hb : a + s ≠ 0)
    (hchar : ∀ x : F, x + x = 0)
    (trace : F → Bool)
    (hadd : ∀ x y : F, trace (x + y) = Bool.xor (trace x) (trace y)) :
    (trace (a * (a * (a + s))⁻¹) = false ∧
     trace (s * (a * (a + s))⁻¹) = false) ↔
    (trace a⁻¹ = false ∧ trace (a + s)⁻¹ = false) := by
  rw [first_source_inverse_identity a s ha,
      second_source_inverse_identity a s ha hb hchar,
      hadd]
  cases trace a⁻¹ <;> cases trace (a + s)⁻¹ <;> decide

#print axioms first_source_inverse_identity
#print axioms second_source_inverse_identity
#print axioms source_trace_conditions_iff
end InverseTraceANF
