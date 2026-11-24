import Std.Tactic.BVDecide

namespace M31SixBitQuotient

-- Clear the pivot by adding the direction, then remove the pivot bit.
def quotient (d x : BitVec 7) : BitVec 6 :=
  let pivot := d &&& (-d)
  let below := pivot - 1
  let y := if x &&& pivot = 0 then x else x ^^^ d
  ((y &&& below) ||| ((y >>> 1) &&& ~~~below)).setWidth 6

theorem linear (d x y : BitVec 7) :
    quotient d (x ^^^ y) = quotient d x ^^^ quotient d y := by
  unfold quotient
  bv_decide

theorem equal_iff (d x y : BitVec 7) (nz : d ≠ 0) :
    quotient d x = quotient d y ↔ x = y ∨ x ^^^ y = d := by
  unfold quotient
  bv_decide

theorem separates {I : Type} (keys : I → BitVec 7) (d : BitVec 7)
    (nz : d ≠ 0) (missing : ∀ i j, keys i ^^^ keys j ≠ d) (i j : I) :
    quotient d (keys i) = quotient d (keys j) ↔ keys i = keys j := by
  rw [equal_iff _ _ _ nz]
  simp [missing]

end M31SixBitQuotient
