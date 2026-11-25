import Std.Tactic.BVDecide
import Mathlib.Tactic

namespace M31CarrySave

abbrev W := BitVec 31
def parity (a b c : W) := a ^^^ b ^^^ c
def majority (a b c : W) := (a &&& b) ||| ((a ^^^ b) &&& c)
def wrap (m : W) := (m <<< 1) ||| (m >>> 30)

-- Both sides below contain at most three 31-bit unsigned quantities.
theorem three_fit (a b c : W) : a.toNat + b.toNat + c.toNat < 2^33 := by
  have := a.isLt
  have := b.isLt
  have := c.isLt
  omega

theorem exact_wide (a b c : W) :
    (a.setWidth 33 + b.setWidth 33 + c.setWidth 33 : BitVec 33) =
      (parity a b c).setWidth 33 + (wrap (majority a b c)).setWidth 33 +
        (if (majority a b c).msb then 2147483647 else 0) := by
  unfold parity majority wrap
  bv_decide

theorem drop_correction (s : Nat) (carry : Bool) :
    (s + (if carry then 2147483647 else 0)) % 2147483647 = s % 2147483647 := by
  cases carry <;> simp

end M31CarrySave
