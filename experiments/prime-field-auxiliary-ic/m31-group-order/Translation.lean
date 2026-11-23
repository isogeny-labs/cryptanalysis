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

end M31Translation
