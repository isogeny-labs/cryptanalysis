import Std
import Init.Grind.Ring.Basic
import Init.Grind.Ring.Field

open Lean.Grind

/-! Algebraic completeness of the S3 quadratic root sets used by the
three-code box intersection gate. -/
namespace TripleBox

theorem s3_as_quadratic {F : Type} [CommRing F]
    (a b t : F) :
    (a*b*t)*(a*b*t) + a*b*t + a*a + b*b + t*t =
      (1+(a*b)*(a*b))*(t*t) + (a*b)*t + (a*a+b*b) := by
  grind +ring

theorem quadratic_root_pair {F : Type} [Field F]
    (A B D x y : F) (hA : A ≠ 0)
    (hx : A*x*x+B*x+D = 0) (hy : A*y*y+B*y+D = 0) :
    y = x ∨ y = -x-B/A := by
  have hfactor : (y-x)*(A*(y+x)+B) = 0 := by
    calc
      (y-x)*(A*(y+x)+B) =
          (A*y*y+B*y+D)-(A*x*x+B*x+D) := by grind +ring
      _ = 0 := by rw [hy,hx]; grind +ring
  rcases Field.of_mul_eq_zero hfactor with hzero | hlinear
  · left
    grind +ring
  · right
    have hmult : A*(y+x) = -B := by
      calc
        A*(y+x) = (A*(y+x)+B)-B := by grind +ring
        _ = -B := by rw [hlinear]; grind +ring
    have hdiv : A*(-B/A) = -B := by
      grind +ring
    have hsum : y+x = -B/A := by
      grind +ring
    calc
      y = (y+x)-x := by grind +ring
      _ = (-B/A)-x := by rw [hsum]
      _ = -x-B/A := by grind +ring

theorem char_two_root_pair {F : Type} [Field F]
    (A B D x y : F) (hA : A ≠ 0)
    (hchar : ∀ z : F, z+z = 0)
    (hx : A*x*x+B*x+D = 0) (hy : A*y*y+B*y+D = 0) :
    y = x ∨ y = x+B/A := by
  have hneg : ∀ z : F, -z = z := by
    intro z
    calc
      -z = -z+(z+z) := by rw [hchar z]; grind +ring
      _ = z := by grind +ring
  rcases quadratic_root_pair A B D x y hA hx hy with h | h
  · exact Or.inl h
  · right
    have hq : -(B/A) = B/A := hneg (B/A)
    calc
      y = -x-B/A := h
      _ = x+B/A := by rw [hneg x]; grind +ring

theorem n131_one_coordinate_payload :
    4294967296 <
      17 * ((16677-4*131)*(16677-(6*131+4))) := by decide

theorem conditional_payload_over_four_gib (eligiblePairs bytes : Nat)
    (hpairs : 256622711 ≤ eligiblePairs)
    (hbytes : 17*eligiblePairs ≤ bytes) :
    4294967296 < bytes := by
  have hn : 4294967296 < 17*256622711 := by decide
  have hm : 17*256622711 ≤ 17*eligiblePairs :=
    Nat.mul_le_mul_left 17 hpairs
  exact Nat.lt_of_lt_of_le hn (Nat.le_trans hm hbytes)

#print axioms s3_as_quadratic
#print axioms quadratic_root_pair
#print axioms char_two_root_pair
#print axioms n131_one_coordinate_payload
#print axioms conditional_payload_over_four_gib

end TripleBox
