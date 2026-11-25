import Std.Tactic.BVDecide

namespace M31SixBitObstruction

def points : List (Nat × Nat) :=
  [(14400,1767351005),(14401,1172913898),(14402,939070711),(14403,1167419731),
   (14404,1838053587),(14405,205390639),(14406,508102077),(14407,1003291763),
   (25984,853207910),(25992,768854607),(26000,380378008),(26008,489956737),
   (26016,531826551),(26024,131339541),(26032,1073578183),(26040,1785161103),
   (3,1729942836)]

def keys := points.map (fun q => BitVec.ofNat 31 q.1)

theorem valid : keys.eraseDups.length = 17 ∧ ∀ q ∈ points,
    q.1 < 2147483647 ∧ q.2 < 2147483647 ∧
    q.2^2 % 2147483647 = (q.1^3 + 2*q.1 + 14) % 2147483647 := by decide +kernel

private def lower (d : BitVec 6) := d &&& 7
private def upper (d : BitVec 6) := d &&& 56

private theorem in_keys : ∀ d : BitVec 6,
    (14400 ^^^ (lower d).setWidth 31) ∈ keys ∧
    (25984 ^^^ (upper d).setWidth 31) ∈ keys := by decide +kernel

private theorem different (d : BitVec 6) :
    (14400 ^^^ (lower d).setWidth 31) ≠ (25984 ^^^ (upper d).setWidth 31) := by
  unfold lower upper
  bv_decide

private theorem meet (a b : BitVec 6) :
    a ^^^ lower (a ^^^ b) = b ^^^ upper (a ^^^ b) := by
  unfold lower upper
  bv_decide

-- Whatever addresses the two high prefixes receive, the low three bits
-- of one group and the next three bits of the other realize their difference.
theorem collision (h : BitVec 31 → BitVec 6)
    (linear : ∀ a b, h (a ^^^ b) = h a ^^^ h b)
    (fixed : ∀ v : BitVec 6, h (v.setWidth 31) = v) :
    ∃ x ∈ keys, ∃ y ∈ keys, x ≠ y ∧ h x = h y := by
  let d := h 14400 ^^^ h 25984
  obtain ⟨left,right⟩ := in_keys d
  refine ⟨_,left,_,right,different d,?_⟩
  rw [linear,linear,fixed,fixed]
  exact meet _ _

-- On this very set a five-bit linear map succeeds if the low-bit
-- identity requirement is lifted. Bits 6 and 7 distinguish the prefixes.
def folded (x : BitVec 31) : BitVec 5 :=
  (((x ^^^ (x >>> 3)) &&& 7) ^^^ ((x >>> 3) &&& 24)).setWidth 5

theorem folded_linear (x y : BitVec 31) : folded (x ^^^ y) = folded x ^^^ folded y := by
  unfold folded
  bv_decide

theorem folded_separates : ∀ x ∈ keys, ∀ y ∈ keys, folded x = folded y → x = y := by
  have pairs : keys.all (fun x => keys.all (fun y => decide (folded x ≠ folded y ∨ x = y))) := by
    decide +kernel
  intro x hx y hy eq
  exact (of_decide_eq_true (List.all_eq_true.mp (List.all_eq_true.mp pairs x hx) y hy)).resolve_left
    (fun ne => ne eq)

end M31SixBitObstruction
