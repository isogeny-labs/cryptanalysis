import Mathlib.GroupTheory.OrderOfElement
import Mathlib.Tactic

namespace M31Translation

/-- On every closed orbit a fixed nonzero increment of coprime order must
fail on at least one edge, even for a completely arbitrary point map. -/
theorem badEdge {G H : Type*} [AddCommGroup G] [AddCommGroup H]
    (f : G → H) (x h : G) (t : H) (m : ℕ) (closed : m • h = 0)
    (cop : Nat.Coprime m (Nat.card H)) (nz : t ≠ 0) :
    ∃ k < m, f (x + k • h + h) ≠ f (x + k • h) + t := by
  by_contra! allGood
  have iter (k : ℕ) (hk : k ≤ m) : f (x + k • h) = f x + k • t := by
    induction k with
    | zero => simp
    | succ k ih =>
      have step := allGood k (by omega)
      rw [succ_nsmul, ← add_assoc, step, ih (by omega), succ_nsmul, add_assoc]
  have endpt := iter m le_rfl
  rw [closed, add_zero] at endpt
  have killed : m • t = 0 := by
    apply add_left_cancel (a := f x)
    simpa using endpt.symm
  have hd := Nat.dvd_gcd (addOrderOf_dvd_iff_nsmul_eq_zero.mpr killed)
    (addOrderOf_dvd_natCard t)
  rw [cop.gcd_eq_one] at hd
  exact nz (AddMonoid.addOrderOf_eq_one_iff.mp (Nat.dvd_one.mp hd))

theorem m31ShortOrbit {G H : Type*} [AddCommGroup G] [AddCommGroup H]
    (targetCard : Nat.card H = 2147505293) (f : G → H) (x h : G)
    (closed : 53 • h = 0) (t : H) (nz : t ≠ 0) :
    ∃ k < 53, f (x + k • h + h) ≠ f (x + k • h) + t := by
  apply badEdge f x h t 53 closed _ nz
  rw [targetCard]
  decide

/-- Index a cycle starting just after its exceptional edge. If the ordinary
edges have the prescribed increment, all 53 vertex values are forced. -/
theorem oneBreakValues {H : Type*} [AddCommGroup H] (f : Fin 53 → H) (t : H)
    (step : ∀ i : Fin 52, f i.succ = f i.castSucc + t) (i : Fin 53) :
    f i = f 0 + i.val • t := by
  induction i using Fin.induction with
  | zero => simp
  | succ i ih => rw [step, ih]; simp [succ_nsmul, add_assoc]

/-- The affine labels give an extremizer for one step. At distance d the
directed step fails precisely at starting indices that wrap around. -/
theorem wrapFailure {H : Type*} [AddCommGroup H] (t : H) (nonzero : 53 • t ≠ 0)
    (i d : Fin 53) :
    ((i + d).val • t ≠ i.val • t + d.val • t) ↔ 53 ≤ i.val + d.val := by
  rw [← add_nsmul]
  change (((i.val + d.val) % 53) • t ≠ (i.val + d.val) • t) ↔ _
  by_cases h : i.val + d.val < 53
  · simp [Nat.mod_eq_of_lt h, Nat.not_le.mpr h]
  · have eqn : i.val + d.val = (i.val + d.val) % 53 + 53 := by
      have := i.isLt
      have := d.isLt
      omega
    refine iff_of_true (fun heq => nonzero ?_) (by omega)
    nth_rw 2 [eqn] at heq
    rw [add_nsmul] at heq
    exact add_left_cancel (a := ((i.val + d.val) % 53) • t) (by simpa using heq.symm)

theorem wrapCount : ∀ d : Fin 53,
    (Finset.univ.filter (fun i : Fin 53 => 53 ≤ i.val + d.val)).card = d.val := by
  decide

/-- For an unordered pair i < j count both directed jumps, using the
positive forward distance around the cycle in each direction. -/
def pairScore {H : Type*} [AddCommGroup H] [DecidableEq H]
    (f : Fin 53 → H) (t : H) (i j : Fin 53) : ℕ :=
  if i < j then
    (if f j = f i + (j.val - i.val) • t then 1 else 0) +
    (if f i = f j + (53 - (j.val - i.val)) • t then 1 else 0)
  else 0

theorem pairScore_le {H : Type*} [AddCommGroup H] [DecidableEq H]
    (f : Fin 53 → H) (t : H) (ht : 53 • t ≠ 0) (i j : Fin 53) :
    pairScore f t i j ≤ (if i < j then 1 else 0) := by
  by_cases hij : i < j
  · simp only [pairScore, hij, ↓reduceIte]
    by_cases forward : f j = f i + (j.val - i.val) • t
    · have backward : f i ≠ f j + (53 - (j.val - i.val)) • t := by
        intro eqn
        rw [forward, add_assoc, ← add_nsmul] at eqn
        have dist : (j.val - i.val) + (53 - (j.val - i.val)) = 53 := by
          have := j.isLt
          omega
        rw [dist] at eqn
        exact ht (add_left_cancel (a := f i) (by simpa using eqn.symm))
      simp only [backward, ↓reduceIte, add_zero]
      simp [forward]
    · simp [forward]
      split <;> decide
  · simp [pairScore, hij]

theorem directedJumpBound {H : Type*} [AddCommGroup H] [DecidableEq H]
    (f : Fin 53 → H) (t : H) (ht : 53 • t ≠ 0) :
    (∑ i, ∑ j, pairScore f t i j) ≤ 1378 := by
  calc
    _ ≤ ∑ i : Fin 53, ∑ j : Fin 53, (if i < j then 1 else 0 : ℕ) :=
      Finset.sum_le_sum fun i _ => Finset.sum_le_sum fun j _ => pairScore_le f t ht i j
    _ = 1378 := by decide

theorem directedJumpSharp {H : Type*} [AddCommGroup H] [DecidableEq H]
    (t : H) (ht : 53 • t ≠ 0) :
    (∑ i, ∑ j, pairScore (fun k => k.val • t) t i j) = 1378 := by
  have scores (i j : Fin 53) :
      pairScore (fun k => k.val • t) t i j = (if i < j then 1 else 0) := by
    apply le_antisymm (pairScore_le _ _ ht _ _)
    by_cases hij : i < j
    · have h : j.val • t = i.val • t + (j.val - i.val) • t := by
        rw [← add_nsmul, Nat.add_sub_of_le (Nat.le_of_lt hij)]
      simp [pairScore, hij, h]
    · simp [hij]
  simp_rw [scores]
  decide

/-- At the optimum every pair is saturated. Subtracting the linear label
then leaves either equal residuals or one downward jump of 53 increments. -/
theorem optimalResidualStep {H : Type*} [AddCommGroup H] [DecidableEq H]
    (f : Fin 53 → H) (t : H) (ht : 53 • t ≠ 0)
    (opt : (∑ i, ∑ j, pairScore f t i j) = 1378)
    (i j : Fin 53) (hij : i < j) :
    f j - j.val • t = f i - i.val • t ∨
    f j - j.val • t = f i - i.val • t - 53 • t := by
  let cap (u v : Fin 53) : ℕ := if u < v then 1 else 0
  have leCap (u v) : pairScore f t u v ≤ cap u v := pairScore_le f t ht u v
  have total : (∑ u, ∑ v, pairScore f t u v) = ∑ u, ∑ v, cap u v :=
    opt.trans (by decide)
  have row := (Finset.sum_eq_sum_iff_of_le (fun u _ =>
    Finset.sum_le_sum (fun v _ => leCap u v))).mp total i (Finset.mem_univ _)
  have pair := (Finset.sum_eq_sum_iff_of_le (fun v _ => leCap i v)).mp row j (Finset.mem_univ _)
  have hlen : j.val • t = i.val • t + (j.val - i.val) • t := by
    rw [← add_nsmul, Nat.add_sub_of_le (Nat.le_of_lt hij)]
  by_cases h : f j = f i + (j.val - i.val) • t
  · left
    rw [h, hlen]
    abel
  · have rev : f i = f j + (53 - (j.val - i.val)) • t := by
      by_contra hn
      simp [pairScore, cap, hij, h, hn] at pair
    have h53 : 53 • t = (j.val - i.val) • t + (53 - (j.val - i.val)) • t := by
      rw [← add_nsmul]
      apply congrArg (fun n : ℕ => n • t)
      have := j.isLt
      omega
    right
    rw [rev, hlen, h53]
    abel

theorem residualCannotRise {H : Type*} [AddCommGroup H] (r : Fin 53 → H) (s : H)
    (hs : s ≠ 0) (hss : s + s ≠ 0)
    (step : ∀ i j : Fin 53, i < j → r j = r i ∨ r j = r i - s)
    (i j : Fin 53) (hij : i < j) (low : r i = r 0 - s) : r j ≠ r 0 := by
  intro high
  rcases step i j hij with eq | eq
  · rw [high, low] at eq
    exact hs (by simpa using eq.symm)
  · rw [high, low, sub_sub] at eq
    exact hss (by simpa using eq.symm)

end M31Translation
