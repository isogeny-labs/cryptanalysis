import Std
import Init.Grind.Ring.Basic

open Lean.Grind

/-! The fixed-seed source product is additive in characteristic two. -/
namespace SourceProductLinear

theorem fixed_seed_product_additive {F : Type} [CommRing F]
    (a b s : F) (hchar : ∀ x : F, x+x = 0) :
    (a+b)*(a+b+s) = a*(a+s)+b*(b+s) := by
  have hab := hchar (a*b)
  grind +ring

theorem frobenius_product_additive {F : Type} [CommRing F]
    (a b s : F) (hchar : ∀ x : F, x+x = 0)
    (frobenius : F → F) (hadd : ∀ x y, frobenius (x+y) = frobenius x + frobenius y) :
    frobenius ((a+b)*(a+b+s)) =
      frobenius (a*(a+s)) + frobenius (b*(b+s)) := by
  rw [fixed_seed_product_additive a b s hchar, hadd]

#print axioms fixed_seed_product_additive
#print axioms frobenius_product_additive

end SourceProductLinear
