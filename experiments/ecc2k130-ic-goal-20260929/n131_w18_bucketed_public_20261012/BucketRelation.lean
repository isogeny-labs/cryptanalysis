/- Structural transport of a checked four-summand equation by a homomorphism.
   The concrete curve and the cofactor map's homomorphism law are outside Lean. -/
import Std

namespace BucketRelation

theorem map_four_sum {G H : Type} [Add G] [Add H]
    (f : G → H) (hom : ∀ x y : G, f (x + y) = f x + f y)
    (a b c d q : G) (h : ((a + b) + c) + d = q) :
    ((f a + f b) + f c) + f d = f q := by
  rw [← hom a b, ← hom (a + b) c, ← hom ((a + b) + c) d, h]

#print axioms BucketRelation.map_four_sum
end BucketRelation
