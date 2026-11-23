import Std.Tactic.BVDecide

namespace M31RotationWindow

/-- With the input in the low 31 bits, a window of the doubled word is the
31-bit right rotation: bits shifted past the low end re-enter at the high end.
Using 64-bit words here matches the native shifts, ORs and mask. -/
theorem window_eq_rotation (x k : BitVec 64)
    (hx : x ≤ 0x7fffffff) (hk : k < 31) :
    ((((x <<< 31) ||| x) >>> k) &&& 0x7fffffff) =
      (((x >>> k) ||| (x <<< (31 - k))) &&& 0x7fffffff) := by
  bv_decide

end M31RotationWindow
