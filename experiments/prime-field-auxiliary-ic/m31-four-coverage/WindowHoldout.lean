import Std

namespace M31WindowHoldout

-- Row 314 of the seed 291161 holdout, in ascending coordinate order.
def keys : List Nat := [498672494, 774333673, 799675276, 819122695, 868942878, 887152135, 902775900, 1020239516, 1108005559, 1151563922, 1177682689, 1527213085, 1676179796, 1678159777, 1808486940, 1866693879, 1867811339]

def occupied (width offset : Nat) :=
  ((keys.map (fun x => (x / 2^offset) % 2^width)).eraseDups).length

theorem distinct_keys : keys.eraseDups.length = 17 := by decide +kernel

-- All contiguous windows contained in a canonical 31-bit word.
set_option maxRecDepth 32768 in
theorem insufficient : ∀ w : Fin 8, ∀ s : Fin 32,
    w.val + s.val ≤ 31 → occupied w.val s.val < 17 := by decide +kernel

theorem sufficient : occupied 8 4 = 17 := by decide +kernel

end M31WindowHoldout
