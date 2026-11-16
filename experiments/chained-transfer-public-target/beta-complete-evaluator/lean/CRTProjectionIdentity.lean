import Std.Tactic

set_option autoImplicit false
namespace CRTProjectionIdentity

-- For ell=4m+1, ell^2-ell is a multiple of the rational annihilator4ell.
-- This is only the scalar identity; the group and geometric bridges are separate.
theorem projection_scalar_identity (m : Int) :
    (4 * m + 1) * (4 * m + 1) - (4 * m + 1) =
      4 * m * (4 * m + 1) := by
  simp only [Int.mul_add, Int.add_mul, Int.mul_one, Int.one_mul]
  omega

end CRTProjectionIdentity
