/-!
# Base-point independence of the discrete logarithm, and arithmetic progressions

Self-contained Lean 4 development (no Mathlib): the algebra is stated over a
minimal additive commutative group so the file checks with the bare toolchain
pinned in `lean-toolchain`.

Setting. `G` is an additive commutative group written additively, as a
subgroup of `E(F_q)` is. Scalars are natural numbers; `n` is the order of the
base point `P`, so `n • P = 0`.

Results.

* `transfer`: if `c · c' ≡ 1 (mod n)` then `(k · c') • (c • P) = k • P`. So a
  logarithm `k` to base `P` is the logarithm `k · c'` to base `P' = c • P`,
  and conversely (`transfer_back`). Any solver for one base point is a solver
  for every other base point of the subgroup at the cost of one scalar
  multiplication and one modular inversion: the base point carries no
  information about `k` that another base point does not.
* `log_unique`: when `P` has exact order `n`, the map `k ↦ k • P` is
  injective on `{0, …, n−1}`. `Q` determines `k` completely, so the
  impossibility of "reading `k` off `Q`" is computational, never
  information-theoretic.
* `ap_const_diff`, `ap_log_shift`: the points `Q_i = (k + i·d) • P` of an
  arithmetic progression of scalars have constant difference `d • P`, and
  each `Q_i` is `Q_0` shifted by a known multiple of that difference. The
  progression therefore exposes exactly one new logarithm (`d`), and nothing
  about `k` beyond what `Q_0` already exposes.
* `ap_sumset_bound` (combinatorial, Nat-level): the pairwise sums of the
  scalars `{1, …, B}` lie in `{2, …, 2B}`, a set of `2B − 1` values, against
  `B(B−1)/2` unordered pairs. This is the collision that made the
  known-log progression factor base of `crypto`'s generator-effect study lose
  a factor `≈ B/4` in relation yield.
-/

/-- Minimal additive commutative group. -/
class AddCommGroupLite (G : Type) extends Add G, Zero G, Neg G where
  add_assoc : ∀ a b c : G, a + b + c = a + (b + c)
  zero_add : ∀ a : G, 0 + a = a
  neg_add_cancel : ∀ a : G, -a + a = 0
  add_comm : ∀ a b : G, a + b = b + a

namespace AddCommGroupLite

variable {G : Type} [AddCommGroupLite G]

theorem add_zero (a : G) : a + 0 = a := by
  rw [add_comm]; exact zero_add a

theorem add_neg_cancel (a : G) : a + -a = 0 := by
  rw [add_comm]; exact neg_add_cancel a

theorem add_left_cancel {a b c : G} (h : a + b = a + c) : b = c := by
  have h2 : -a + (a + b) = -a + (a + c) := by rw [h]
  rw [← add_assoc, ← add_assoc, neg_add_cancel, zero_add, zero_add] at h2
  exact h2

theorem add_right_cancel {a b c : G} (h : b + a = c + a) : b = c := by
  rw [add_comm b, add_comm c] at h
  exact add_left_cancel h

/-- Natural scalar multiplication `k • P`. -/
def nsmul : Nat → G → G
  | 0, _ => 0
  | k + 1, P => nsmul k P + P

infixr:73 " • " => nsmul

@[simp] theorem zero_smul (P : G) : (0 : Nat) • P = 0 := rfl
theorem succ_smul (k : Nat) (P : G) : (k + 1) • P = k • P + P := rfl

theorem add_smul (a b : Nat) (P : G) : (a + b) • P = a • P + b • P := by
  induction b with
  | zero => simp [nsmul, add_zero]
  | succ b ih =>
    rw [Nat.add_succ, succ_smul, succ_smul, ih, add_assoc]

theorem one_smul (P : G) : (1 : Nat) • P = P := by
  show (0 : Nat) • P + P = P
  rw [zero_smul, zero_add]

theorem smul_zero (k : Nat) : k • (0 : G) = 0 := by
  induction k with
  | zero => rfl
  | succ k ih => rw [succ_smul, ih, add_zero]

theorem smul_add (k : Nat) (P Q : G) : k • (P + Q) = k • P + k • Q := by
  induction k with
  | zero => simp [nsmul, add_zero]
  | succ k ih =>
    rw [succ_smul, succ_smul, succ_smul, ih]
    rw [add_assoc, add_assoc]
    congr 1
    rw [← add_assoc, add_comm (k • Q) P, add_assoc]

theorem mul_smul (a b : Nat) (P : G) : (a * b) • P = a • (b • P) := by
  induction a with
  | zero => simp [nsmul]
  | succ a ih =>
    rw [Nat.succ_mul, add_smul, ih, succ_smul]

/-- `n • P = 0`: `n` is a multiple of the order of `P`. -/
def Annihilates (n : Nat) (P : G) : Prop := n • P = 0

theorem smul_mul_annihilates {n : Nat} {P : G} (h : Annihilates n P) (q : Nat) :
    (n * q) • P = 0 := by
  rw [Nat.mul_comm, mul_smul, h, smul_zero]

/-- Scalars congruent modulo an annihilator give the same point. -/
theorem smul_mod {n : Nat} {P : G} (h : Annihilates n P) (k : Nat) :
    k • P = (k % n) • P := by
  have hk : k = k % n + n * (k / n) := (Nat.mod_add_div k n).symm
  calc k • P = (k % n + n * (k / n)) • P := by rw [← hk]
    _ = (k % n) • P := by rw [add_smul, smul_mul_annihilates h, add_zero]

/-! ### Base-point independence -/

/-- **Transfer.** If `c · c' ≡ 1 (mod n)` and `n • P = 0`, then the logarithm
`k` of `Q = k • P` to base `P` becomes the logarithm `k · c'` to the base
`P' = c • P`: `(k · c') • (c • P) = k • P`. -/
theorem transfer {n c c' : Nat} {P : G} (hn : Annihilates n P)
    (hc : (c * c') % n = 1 % n) (k : Nat) :
    (k * c') • (c • P) = k • P := by
  rw [← mul_smul, Nat.mul_assoc, Nat.mul_comm c' c, mul_smul, smul_mod hn (c * c'), hc,
    ← smul_mod hn 1, one_smul]

/-- **Transfer, solver form.** A logarithm `k'` of `Q` to the base `c • P`
yields the logarithm `k' · c` of `Q` to the base `P`, with no hypothesis on
`c` at all. -/
theorem transfer_back {c k' : Nat} {P Q : G} (h : k' • (c • P) = Q) :
    (k' * c) • P = Q := by
  rw [mul_smul]; exact h

/-- **Base points of the subgroup are interchangeable.** For `c` invertible
modulo `n`, `k ↦ k · c' mod n` is a bijection of residues carrying logarithms
to base `P` onto logarithms to base `c • P`, and `k' ↦ k' · c mod n` is its
inverse (`transfer` and `transfer_back` together). -/
theorem transfer_roundtrip {n c c' : Nat} {P : G} (hn : Annihilates n P)
    (hc : (c * c') % n = 1 % n) (k : Nat) :
    ((k * c') * c) • P = k • P := by
  rw [mul_smul]
  exact transfer hn hc k

/-! ### The logarithm is information-theoretically determined -/

/-- `P` has exact order `n`: `n • P = 0` and no smaller positive multiple vanishes. -/
structure ExactOrder (n : Nat) (P : G) : Prop where
  annihilates : Annihilates n P
  minimal : ∀ m, 0 < m → m < n → m • P ≠ 0

theorem smul_sub_eq_zero {a b : Nat} {P : G} (hab : a ≤ b) (h : a • P = b • P) :
    (b - a) • P = 0 := by
  have hb : b = a + (b - a) := (Nat.add_sub_cancel' hab).symm
  rw [hb, add_smul] at h
  have h0 : a • P + 0 = a • P + (b - a) • P := by rw [add_zero]; exact h
  exact (add_left_cancel h0).symm

/-- **Uniqueness.** With `P` of exact order `n`, residues below `n` with the
same multiple are equal: `Q = k • P` determines `k`. -/
theorem log_unique {n : Nat} {P : G} (hP : ExactOrder n P) {k₁ k₂ : Nat}
    (h₁ : k₁ < n) (h₂ : k₂ < n) (h : k₁ • P = k₂ • P) : k₁ = k₂ := by
  rcases Nat.le_total k₁ k₂ with hle | hle
  · have hz := smul_sub_eq_zero hle h
    apply Decidable.byContradiction
    intro hne
    have hpos : 0 < k₂ - k₁ := Nat.sub_pos_of_lt (Nat.lt_of_le_of_ne hle hne)
    have hlt : k₂ - k₁ < n := Nat.lt_of_le_of_lt (Nat.sub_le _ _) h₂
    exact hP.minimal _ hpos hlt hz
  · have hz := smul_sub_eq_zero hle h.symm
    apply Decidable.byContradiction
    intro hne
    have hpos : 0 < k₁ - k₂ := Nat.sub_pos_of_lt (Nat.lt_of_le_of_ne hle (Ne.symm hne))
    have hlt : k₁ - k₂ < n := Nat.lt_of_le_of_lt (Nat.sub_le _ _) h₁
    exact hP.minimal _ hpos hlt hz

/-! ### Arithmetic progressions of scalars -/

/-- The `i`-th point of the progression with start `k` and step `d`. -/
def apPoint (k d : Nat) (P : G) (i : Nat) : G := (k + i * d) • P

/-- **Constant difference.** Consecutive points of the progression differ by
the fixed point `D = d • P`. -/
theorem ap_const_diff (k d : Nat) (P : G) (i : Nat) :
    apPoint k d P (i + 1) = apPoint k d P i + d • P := by
  unfold apPoint
  rw [Nat.succ_mul, ← Nat.add_assoc, add_smul]

/-- **Known shift.** Every point of the progression is the first point plus a
known multiple of the common difference: `Q_i = Q_0 + i • D`. Given `Q_0` and
`D`, the rest of the progression carries no further information about `k`. -/
theorem ap_log_shift (k d : Nat) (P : G) (i : Nat) :
    apPoint k d P i = apPoint k d P 0 + i • (d • P) := by
  unfold apPoint
  rw [Nat.zero_mul, Nat.add_zero, add_smul, mul_smul]

/-- **Difference is one logarithm.** The step `D = Q_1 − Q_0` is `d • P`:
solving a single DLP for `D` reveals `d`, and conversely nothing in the
differences depends on `k`. -/
theorem ap_diff_indep_of_start (k k' d : Nat) (P : G) (i : Nat) :
    apPoint k d P (i + 1) + -(apPoint k d P i)
      = apPoint k' d P (i + 1) + -(apPoint k' d P i) := by
  rw [ap_const_diff, ap_const_diff]
  rw [add_comm (apPoint k d P i), add_assoc, add_neg_cancel, add_zero]
  rw [add_comm (apPoint k' d P i), add_assoc, add_neg_cancel, add_zero]

/-! ### Sumset collapse of a progression base (Nat level) -/

/-- Pairwise sums of scalars from `{1, …, B}` lie in `{2, …, 2B}`. -/
theorem ap_sumset_bound {B i j : Nat} (hi : 1 ≤ i) (hi' : i ≤ B) (hj : 1 ≤ j) (hj' : j ≤ B) :
    2 ≤ i + j ∧ i + j ≤ 2 * B := by
  constructor <;> omega

/-- The progression base `{[1]P, …, [B]P}` has a pairwise sumset inside
`{[2]P, …, [2B]P}`: at most `2B − 1` distinct points, however the base is
embedded in the group. -/
theorem ap_base_sum_mem {B i j : Nat} (P : G) (hi : 1 ≤ i) (hi' : i ≤ B)
    (hj : 1 ≤ j) (hj' : j ≤ B) :
    ∃ s, 2 ≤ s ∧ s ≤ 2 * B ∧ i • P + j • P = s • P := by
  refine ⟨i + j, (ap_sumset_bound hi hi' hj hj').1, (ap_sumset_bound hi hi' hj hj').2, ?_⟩
  rw [add_smul]

end AddCommGroupLite

open AddCommGroupLite in
/-- Sanity instance: the integers form such a group, so the development is
not vacuous. -/
instance : AddCommGroupLite Int where
  add_assoc := Int.add_assoc
  zero_add := Int.zero_add
  neg_add_cancel := Int.add_left_neg
  add_comm := Int.add_comm

/-! Axiom audit: one line per theorem, required by the corpus gate. -/
#print axioms AddCommGroupLite.add_zero
#print axioms AddCommGroupLite.add_neg_cancel
#print axioms AddCommGroupLite.add_left_cancel
#print axioms AddCommGroupLite.add_right_cancel
#print axioms AddCommGroupLite.succ_smul
#print axioms AddCommGroupLite.add_smul
#print axioms AddCommGroupLite.one_smul
#print axioms AddCommGroupLite.smul_zero
#print axioms AddCommGroupLite.smul_add
#print axioms AddCommGroupLite.mul_smul
#print axioms AddCommGroupLite.smul_mul_annihilates
#print axioms AddCommGroupLite.smul_mod
#print axioms AddCommGroupLite.transfer
#print axioms AddCommGroupLite.transfer_back
#print axioms AddCommGroupLite.transfer_roundtrip
#print axioms AddCommGroupLite.smul_sub_eq_zero
#print axioms AddCommGroupLite.log_unique
#print axioms AddCommGroupLite.ap_const_diff
#print axioms AddCommGroupLite.ap_log_shift
#print axioms AddCommGroupLite.ap_diff_indep_of_start
#print axioms AddCommGroupLite.ap_sumset_bound
#print axioms AddCommGroupLite.ap_base_sum_mem
