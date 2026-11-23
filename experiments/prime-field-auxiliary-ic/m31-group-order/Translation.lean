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

end M31Translation
