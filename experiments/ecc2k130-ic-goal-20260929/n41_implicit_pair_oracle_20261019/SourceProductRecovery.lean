import Std
import Init.Grind.Ring.Basic

namespace SourceProductRecovery
open Lean.Grind

/-- A nonzero reciprocal pair coordinate determines the source product.
    The statement keeps the characteristic-two and nonzero assumptions
    explicit. -/
theorem recover_product {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (C H p z : F) (hz : z ≠ 0)
    (hroot : C*z^2 + p*z + H = 0) :
    p = C*z + H*z⁻¹ := by
  have hcancel := charTwo (C*z^2+H)
  grind +ring

#print axioms recover_product

/-- A source-product membership test can reject an entire second-pair
    family without enumerating its points. -/
theorem reject_outside_span {F : Type} [Field F]
    (charTwo : ∀ x : F, x + x = 0)
    (InSpan : F → Prop) (C H p z : F) (hz : z ≠ 0)
    (hroot : C*z^2 + p*z + H = 0)
    (hsource : InSpan p)
    (houtside : ¬ InSpan (C*z + H*z⁻¹)) : False := by
  have hrec := recover_product charTwo C H p z hz hroot
  rw [hrec] at hsource
  exact houtside hsource

#print axioms reject_outside_span

end SourceProductRecovery
