import Std.Tactic
set_option autoImplicit false
namespace QuadraticNormIdentity

theorem norm_multiplicative (a b c d n : Int) :
    (a*c+n*b*d)*(a*c+n*b*d) - n*((a*d+b*c)*(a*d+b*c)) =
      (a*a-n*b*b)*(c*c-n*d*d) := by
  simp only [Int.mul_add, Int.add_mul, Int.mul_sub, Int.sub_mul]
  simp only [Int.mul_comm, Int.mul_left_comm]
  omega

end QuadraticNormIdentity
