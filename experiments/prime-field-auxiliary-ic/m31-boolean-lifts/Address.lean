import Std

namespace M31FixtureAddress

private def base : List UInt32 := [3, 98625645, 308768278, 536276641, 753804470, 975624154, 985108144, 1171458932, 1213058799, 1393679185, 1685732321, 1760557235, 1896314920, 1900239952, 1900319349, 1908835095, 2084456163]
private def other : List UInt32 := [80168778, 141165527, 845665662, 987367763, 1101836261, 1431655765, 1491270739, 1528659296, 1533993268, 1560638367, 1620095117, 1851652048, 1857409341, 1950178058, 2008905047]

private def separates (m : UInt32) : Bool :=
  let keys := base.map (fun x => x &&& m)
  keys.eraseDups.length == base.length && other.all (fun x => !keys.contains (x &&& m))

/-- Each choice of five positions occurs once, in strictly descending order. -/
private def fiveBitCandidate : Bool :=
  (List.range 31).any fun a => (List.range a).any fun b =>
    (List.range b).any fun c => (List.range c).any fun d => (List.range d).any fun e =>
      separates ((1 <<< a.toUInt32) ||| (1 <<< b.toUInt32) ||| (1 <<< c.toUInt32) |||
                 (1 <<< d.toUInt32) ||| (1 <<< e.toUInt32))

theorem no_five_bit_address : fiveBitCandidate = false := by native_decide

/-- Bits 0, 1, 6, 7, 8 and 26 distinguish all 32 fixture coordinates. -/
theorem six_bit_address :
    let m : UInt32 := 2^0 + 2^1 + 2^6 + 2^7 + 2^8 + 2^26
    separates m = true ∧ ((base ++ other).map (fun x => x &&& m)).eraseDups.length = 32 := by
  native_decide

end M31FixtureAddress
