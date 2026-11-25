import Mathlib.NumberTheory.SmoothNumbers
import Mathlib.Data.Nat.Factorial.Basic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.RingTheory.RootsOfUnity.PrimitiveRoots
import Mathlib.Tactic.ReduceModChar

namespace M31LevelTwo

abbrev p : ℕ := 2147483647
abbrev F := ZMod p

local instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private theorem primitive : IsPrimitiveRoot (2 : F) 31 := by
  let : Fact (Nat.Prime 31) := ⟨by decide⟩
  apply IsPrimitiveRoot.iff_orderOf.mpr
  apply orderOf_eq_prime <;> decide

def siblings : Fin 8 → ℕ × ℕ
  | 0 => (6, 1431655766)
  | 1 => (70119724, 289112341)
  | 2 => (400522481, 1697529749)
  | 3 => (640084933, 872446386)
  | 4 => (778318563, 1312624457)
  | 5 => (922984491, 1649071223)
  | 6 => (1632618911, 1700263893)
  | 7 => (1713073446, 1830773804)

def scale (neg : Bool) := if neg then p-16384 else 16384

def word (neg : Bool) (x : ℕ) (i : Fin 31) :=
  ((scale neg : F) * (x : F) * 2^i.val).val

/-- A divisor greater than one, coprime to b!, forces a prime factor above b. -/
theorem obstruction {b n d : ℕ} (hd : 1 < d) (hn : d ∣ n)
    (hg : d.gcd b.factorial = 1) : n ∉ Nat.smoothNumbers (b+1) := by
  intro h
  have hp := Nat.minFac_prime (by omega : d ≠ 1)
  have hdn := Nat.minFac_dvd d
  have hsmall := Nat.mem_smoothNumbers'.mp h _ hp (hdn.trans hn)
  have hf := Nat.dvd_factorial hp.pos (by omega : d.minFac ≤ b)
  have hone := Nat.dvd_gcd hdn hf
  rw [hg] at hone
  exact hp.not_dvd_one hone

private def blocked (n : ℕ) : Prop :=
  let d := n / n.gcd ((Nat.factorial 210)^31)
  1 < d ∧ d ∣ n ∧ d.gcd (Nat.factorial 210) = 1

private instance (n : ℕ) : Decidable (blocked n) := by unfold blocked; infer_instance

set_option maxRecDepth 65536 in
set_option maxHeartbeats 8000000 in
private theorem certificate : ∀ j : Fin 8, ∀ neg : Bool,
    (∀ i : Fin 31, blocked (word neg (siblings j).1 i)) ∨
    (∀ i : Fin 31, blocked (word neg (siblings j).2 i)) := by
  decide +kernel

theorem lower (j : Fin 8) (neg : Bool) (i k : Fin 31) :
    ¬ (word neg (siblings j).1 i ∈ Nat.smoothNumbers 211 ∧
       word neg (siblings j).2 k ∈ Nat.smoothNumbers 211) := by
  intro ⟨hu, hv⟩
  rcases certificate j neg with h | h
  · obtain ⟨hd,hn,hg⟩ := h i
    exact obstruction hd hn hg hu
  · obtain ⟨hd,hn,hg⟩ := h k
    exact obstruction hd hn hg hv

theorem upper :
    word false (siblings 6).1 16 ∈ Nat.smoothNumbers 212 ∧
    word false (siblings 6).2 7 ∈ Nat.smoothNumbers 212 := by
  decide +kernel

set_option maxRecDepth 65536 in
theorem eligible :
    let x : F := scale false * (siblings 6).1
    let y : F := scale false * (siblings 6).2
    x*y = 1 ∧ x^1073741823 = -1 ∧ x^31 ≠ y^31 := by
  dsimp [scale, siblings, F, p]
  constructor
  · decide +kernel
  constructor
  · reduce_mod_char
  · decide +kernel

/-- Every compatible scale differs from one of the two normalized choices
by a rotation. -/
theorem normalized (s : F) (hs : (s^2*8)^31 = 1) :
    ∃ neg : Bool, ∃ j : Fin 31, s = (scale neg : F) * 2^j.val := by
  obtain ⟨i, hi, he⟩ := primitive.eq_pow_of_pow_eq_one hs
  have roots : ∀ i : Fin 31, ∃ j : Fin 31,
      (16384 * (2:F)^j.val)^2 * 8 = 2^i.val := by decide +kernel
  obtain ⟨j, hj⟩ := roots ⟨i, hi⟩
  have hsq : s^2 = (16384 * (2:F)^j.val)^2 := by
    apply (mul_left_inj' (by decide : (8:F) ≠ 0)).mp
    exact he.symm.trans hj.symm
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp hsq with h | h
  · exact ⟨false, j, h⟩
  · refine ⟨true, j, ?_⟩
    rw [show (scale true : F) = -16384 by decide, neg_mul]
    exact h

private theorem shifted_word (neg : Bool) (x : ℕ) (i j : Fin 31) :
    (((scale neg : F)*2^j.val) * (x:F) * 2^i.val).val =
      word neg x ⟨(j.val+i.val)%31, Nat.mod_lt _ (by decide)⟩ := by
  unfold word
  congr 1
  have hr := pow_mod_orderOf (2:F) (j.val+i.val)
  rw [← primitive.eq_orderOf, pow_add] at hr
  rw [hr]
  ring

theorem compatible_lower (s : F) (hs : (s^2*8)^31 = 1)
    (j : Fin 8) (i k : Fin 31) :
    ¬ ((s * (siblings j).1 * 2^i.val).val ∈ Nat.smoothNumbers 211 ∧
       (s * (siblings j).2 * 2^k.val).val ∈ Nat.smoothNumbers 211) := by
  obtain ⟨neg, t, rfl⟩ := normalized s hs
  rw [shifted_word, shifted_word]
  apply lower

/-- A reciprocal-compatible, eligible pair has representatives smooth at
inclusive bound b precisely when b reaches 211. -/
def feasible (b : ℕ) : Prop :=
  ∃ (s : F) (j : Fin 8) (i k : Fin 31), (s^2*8)^31 = 1 ∧
    (s*(siblings j).1)^1073741823 = -1 ∧
    (s*(siblings j).1)^31 ≠ (s*(siblings j).2)^31 ∧
    (s*(siblings j).1*2^i.val).val ∈ Nat.smoothNumbers (b+1) ∧
    (s*(siblings j).2*2^k.val).val ∈ Nat.smoothNumbers (b+1)

theorem exact_threshold (b : ℕ) : feasible b ↔ 211 ≤ b := by
  constructor
  · rintro ⟨s,j,i,k,hs,_,_,hu,hv⟩
    by_contra! h
    have mono := Nat.smoothNumbers_mono (show b+1 ≤ 211 by omega)
    exact compatible_lower s hs j i k ⟨mono hu, mono hv⟩
  · intro h
    have mono := Nat.smoothNumbers_mono (show 212 ≤ b+1 by omega)
    exact ⟨(scale false : F), 6, 16, 7, by decide +kernel,
      eligible.2.1, eligible.2.2, mono upper.1, mono upper.2⟩

end M31LevelTwo
#print axioms M31LevelTwo.exact_threshold
