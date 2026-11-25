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

theorem complement_fold (hi lo : BitVec 32) :
    hi - (2147483647 &&& ~~~lo) = hi + ((lo &&& 2147483647) - 2147483647) := by
  bv_decide

/-- Substitution in a whole square-root chain, including lanes represented by negative words.
The two implementations share the multiply-high and multiply-low operations. -/
theorem complement_chain (high low : BitVec 32 → BitVec 32) (n : Nat) (x : BitVec 32) :
    (fun v => high v - (2147483647 &&& ~~~(low v)))^[n] x =
    (fun v => high v + ((low v &&& 2147483647) - 2147483647))^[n] x := by
  have same : (fun v => high v - (2147483647 &&& ~~~(low v))) =
      (fun v => high v + ((low v &&& 2147483647) - 2147483647)) :=
    funext fun v => complement_fold (high v) (low v)
  rw [same]

def quad (x : BitVec 31) :=
  triple x &&& ~~~(x ^^^ ((x.rotateLeft 1).rotateLeft 1).rotateLeft 1)

theorem quad_fallback (x : BitVec 31) (lo : x ≠ 0) (hi : x ≠ 2147483647) :
    ((x ^^^ x.rotateRight 1) &&& quad x = 0) ↔ quad x = 0 := by
  unfold quad triple
  bv_decide

theorem quad_address (x : BitVec 31) (i : Fin 31)
    (mark : (((x ^^^ x.rotateRight 1) &&& quad x) >>> i.val) &&& 1 = 1) :
    let v := if (x >>> i.val) &&& 1 = 0 then x else ~~~x
    v.rotateRight (i.val+1) &&& 2013265921 = 1 := by
  unfold quad triple at mark
  fin_cases i <;> simp only [Nat.reduceAdd] at * <;> bv_decide

theorem three_character (a : F) : quadraticChar F (3*a) = -quadraticChar F a := by
  have eq : (3 : F) = (-1) * (1268011823 : F)^2 := by decide +kernel
  rw [map_mul, eq, map_mul, quadraticChar_sq_one' (by decide +kernel : (1268011823 : F) ≠ 0),
    quadraticChar_neg_one_iff_not_isSquare.mpr M31FiberLift.minus_one_nonsquare]
  ring

theorem quad_rotate (x : BitVec 31) :
    quad (x.rotateRight 1) = (quad x).rotateRight 1 := by
  unfold quad triple
  bv_decide

theorem quad_complement (x : BitVec 31) : quad (~~~x) = quad x := by
  unfold quad triple
  bv_decide

/-- Normalization after a three-bit match on a four-bit miss fixes another address bit. -/
theorem secondary_high (v : BitVec 31) (miss : quad v = 0)
    (headBits : v &&& 1879048193 = 1) : v &&& 2013265921 = 134217729 := by
  unfold quad triple at miss
  bv_decide

theorem interior_nibble (v : BitVec 31) (miss : quad v = 0) (i : BitVec 5) (bound : i ≤ 27) :
    let bits := (v >>> i) &&& 15
    bits ≠ 0 ∧ bits ≠ 15 := by
  unfold quad triple at miss
  bv_decide

def validNine (x : Nat) : Bool :=
  (List.range 6).all fun k =>
    let nibble := (x / 2^k) % 16
    nibble != 0 && nibble != 15

theorem nine_counts :
    ((List.range 256).filter validNine).length = 149 ∧
    ((List.range 512).filter validNine).length = 298 := by decide +kernel

theorem packed_digits (a b c d e f : Nat)
    (ha : a < 298) (hb : b < 298) (hc : c < 149)
    (hd : d < 298) (he : e < 298) :
    ((c * 298 + b) * 298 + a < 13231796) ∧
    (((c * 298 + b) * 298 + a = (f * 298 + e) * 298 + d) ↔
      a = d ∧ b = e ∧ c = f) := by omega

theorem bytes : (34636833 + 7) / 8 = 4329605 := by decide
end M31ResidueOrbits
