import Std.Tactic.BVDecide
import FiberLift
import Mathlib.GroupTheory.Index
import Mathlib.GroupTheory.OrderOfElement

namespace M31ResidueOrbits
abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def generator : Fˣ := Units.mk0 (-2) (by decide +kernel)

theorem period : orderOf generator = 62 := by
  apply (orderOf_eq_iff (by decide : 0 < 62)).mpr
  constructor
  · apply Units.ext
    decide +kernel
  · have check : ∀ i : Fin 62, i.val = 0 ∨ ((-2 : F)^i.val ≠ 1) := by decide +kernel
    intro m hm pos h
    have eq := congrArg Units.val h
    exact ((check ⟨m,hm⟩).resolve_left (Nat.ne_of_gt pos)) (by simpa [generator] using eq)

theorem orbit_count : (Subgroup.zpowers generator).index = 34636833 := by
  have h := (Subgroup.zpowers generator).index_mul_card
  have groupSize : Nat.card Fˣ = 2147483646 := by
    exact Nat.card_eq_fintype_card.trans (ZMod.card_units 2147483647)
  rw [Nat.card_zpowers, period, groupSize] at h
  omega

theorem character (a : F) (k : Nat) :
    quadraticChar F (((-2:F)^k)*a) = (-1 : ℤ)^k * quadraticChar F a := by
  have two : quadraticChar F 2 = 1 := by
    have eq : (65536 : F)^2 = 2 := by decide +kernel
    rw [← eq]
    exact quadraticChar_sq_one' (by decide +kernel)
  have negOne := quadraticChar_neg_one_iff_not_isSquare.mpr M31FiberLift.minus_one_nonsquare
  have negTwo : quadraticChar F (-2) = -1 := by
    rw [← neg_one_mul (2:F), map_mul, negOne, two, mul_one]
  rw [map_mul, map_pow, negTwo]

theorem marker_exists (x : BitVec 31) (lo : x ≠ 0) (hi : x ≠ 2147483647) :
    ((x ^^^ x.rotateRight 1) &&& ~~~(x ^^^ x.rotateLeft 1)) ≠ 0 := by bv_decide

theorem rotate_value (x : Nat) (h : x < 2147483647) :
    (2*x) % 2147483648 + x/1073741824 = (2*x) % 2147483647 := by
  by_cases small : x < 1073741824
  · rw [Nat.div_eq_of_lt small, Nat.mod_eq_of_lt (by omega : 2*x < 2147483648),
        Nat.mod_eq_of_lt (by omega : 2*x < 2147483647)]
    omega
  · have div : x / 1073741824 = 1 := by omega
    rw [div, Nat.mod_eq_sub_mod (by omega : 2147483648 ≤ 2*x),
        Nat.mod_eq_sub_mod (by omega : 2147483647 ≤ 2*x),
        Nat.mod_eq_of_lt (by omega : 2*x-2147483648 < 2147483648),
        Nat.mod_eq_of_lt (by omega : 2*x-2147483647 < 2147483647)]
    omega

theorem selected_bits (x : BitVec 31) (i : Fin 31)
    (mark : (((x ^^^ x.rotateRight 1) &&& ~~~(x ^^^ x.rotateLeft 1)) >>> i.val) &&& 1 = 1) :
    let v := if (x >>> i.val) &&& 1 = 0 then x else ~~~x
    v.rotateRight (i.val+1) &&& 1610612737 = 1 := by
  fin_cases i <;> simp only [Nat.reduceAdd] at * <;> bv_decide

def triple (x : BitVec 31) :=
  ~~~(x ^^^ x.rotateLeft 1) &&& ~~~(x ^^^ (x.rotateLeft 1).rotateLeft 1)

theorem triple_fallback (x : BitVec 31) (lo : x ≠ 0) (hi : x ≠ 2147483647) :
    ((x ^^^ x.rotateRight 1) &&& triple x = 0) ↔ triple x = 0 := by
  unfold triple
  bv_decide

theorem triple_address (x : BitVec 31) (i : Fin 31)
    (mark : (((x ^^^ x.rotateRight 1) &&& triple x) >>> i.val) &&& 1 = 1) :
    let v := if (x >>> i.val) &&& 1 = 0 then x else ~~~x
    v.rotateRight (i.val+1) &&& 1879048193 = 1 := by
  unfold triple at mark
  fin_cases i <;> simp only [Nat.reduceAdd] at * <;> bv_decide

theorem bytes : (34636833 + 7) / 8 = 4329605 := by decide
end M31ResidueOrbits
