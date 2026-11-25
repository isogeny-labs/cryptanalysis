import Mathlib.Tactic
import Std.Tactic.BVDecide

namespace M31ResidueBuild

/-- The aligned root grid adds only zero to the scalar builder's range. -/
theorem root_grid (y : Nat) :
    y ≤ 2147483647 / 2 ↔ ∃ block lane : Nat,
      block < 67108864 ∧ lane < 16 ∧ y = 16 * block + lane := by
  constructor
  · intro h
    exact ⟨y/16, y%16, by omega, by omega, by omega⟩
  · rintro ⟨b,l,hb,hl,rfl⟩
    omega

theorem grid_unique (b c i j : Nat) (hi : i < 16) (hj : j < 16)
    (same : 16*b+i = 16*c+j) : b=c ∧ i=j := by omega

/-- The direct tables use 27, 28 or 29 accepted residue bits. The packed
layout uses the 28-bit filter before dispatch to the two output arrays. -/
theorem filters (r : BitVec 32) :
    ((r &&& 0xf8000001 = 1) ↔ r < 0x08000000 ∧ r &&& 1 = 1) ∧
    ((r &&& 0xf0000001 = 1) ↔ r < 0x10000000 ∧ r &&& 1 = 1) ∧
    ((r &&& 0xe0000001 = 1) ↔ r < 0x20000000 ∧ r &&& 1 = 1) := by
  bv_decide

/-- The horizontal NEON sum concatenates sixteen lane flags without carry. -/
theorem interleaved_sum (a b c d : BitVec 32) :
    let w := a &&& 0x1111
    let x := b &&& 0x2222
    let y := c &&& 0x4444
    let z := d &&& 0x8888
    w + x + y + z = w ||| x ||| y ||| z := by bv_decide

def equalWindows (r : BitVec 32) :=
  let eq := ~~~(r ^^^ (r >>> 1))
  eq &&& (eq >>> 1) &&& (eq >>> 2)

def validBlock (block : BitVec 32) :=
  (equalWindows block &&& 63) = 0

theorem packed_windows (r : BitVec 32) :
    (equalWindows r &&& 0x1f8fc7e = 0) ↔
    validBlock ((r >>> 1) &&& 511) ∧ validBlock ((r >>> 10) &&& 511) ∧
    validBlock ((r >>> 19) &&& 511) := by
  unfold validBlock equalWindows
  bv_decide

theorem window_zero (r : BitVec 32) :
    (equalWindows r &&& 1 = 1) ↔ (r &&& 15 = 0 ∨ r &&& 15 = 15) := by
  unfold equalWindows
  bv_decide

end M31ResidueBuild
