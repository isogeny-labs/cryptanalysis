import Std.Tactic.BVDecide
namespace M31PrimeLanes
abbrev W := BitVec 32

/-- Each physical lane collects one bit from each group of four primes.
Horizontal addition returns their union without a carry. -/
theorem horizontal_mask (a b c d : W)
    (ha : a &&& 0x1111 = a) (hb : b &&& 0x2222 = b)
    (hc : c &&& 0x4444 = c) (hd : d &&& 0x8888 = d) :
    a + b + c + d = a ||| b ||| c ||| d := by bv_decide

end M31PrimeLanes
