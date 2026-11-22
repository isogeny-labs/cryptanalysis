import Std
import Init.Grind.Ring.Basic

namespace PairOutputRecovery
open Lean.Grind

/-- The fixed-seed source-product map is additive in characteristic two. -/
theorem fixed_seed_product_additive {F : Type} [CommRing F]
    (a b s : F) (hchar : ∀ x : F, x + x = 0) :
    (a + b) * (a + b + s) = a * (a + s) + b * (b + s) := by
  have hcross := hchar (a * b)
  grind

/-- For a nonzero pair output, the fixed-seed quadratic determines its
source product uniquely. The native decoder evaluates this inverse and
then tests membership in the linearized source-product image. -/
theorem source_product_unique {F : Type} [Field F]
    (C H c p q : F) (hc : c ≠ 0)
    (hp : C * c * c + p * c + H = 0)
    (hq : C * c * c + q * c + H = 0) : p = q := by
  have heq : p * c = q * c := by
    grind
  grind

/-- In characteristic two the unique product has the implemented formula. -/
theorem recover_source_product {F : Type} [Field F]
    (C H c p : F) (hc : c ≠ 0)
    (hchar : ∀ x : F, x + x = 0)
    (hpair : C * c * c + p * c + H = 0) :
    p = (C * c * c + H) / c := by
  have htwice := hchar (C * c * c + H)
  grind

#print axioms PairOutputRecovery.fixed_seed_product_additive
#print axioms PairOutputRecovery.source_product_unique
#print axioms PairOutputRecovery.recover_source_product

end PairOutputRecovery
