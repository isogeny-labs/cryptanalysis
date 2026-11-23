import Mathlib

namespace M31TransportedRows

variable {G H I : Type*} [AddCommGroup G] [AddCommGroup H]

/-- On an n-torsion source, an isogeny is faithful when its dual composes
to [degree] and the degree is coprime to n. The dual can take values in a
larger group containing the source; only the kernel implication is needed. -/
theorem faithful (φ : G →+ H) {n degree : ℕ} (cop : n.Coprime degree)
    (torsion : ∀ x : G, n • x = 0)
    (kernel : ∀ x, φ x = 0 → degree • x = 0) : Function.Injective φ := by
  intro x y h
  have zero : φ (x-y) = 0 := by rw [map_sub,h,sub_self]
  have hn := addOrderOf_dvd_iff_nsmul_eq_zero.mpr (torsion (x-y))
  have hd := addOrderOf_dvd_iff_nsmul_eq_zero.mpr (kernel (x-y) zero)
  exact sub_eq_zero.mp (AddMonoid.addOrderOf_eq_one_iff.mp
    (Nat.dvd_one.mp (cop ▸ Nat.dvd_gcd hn hd)))

def evalRow (base : I → G) (r : List (I × ℤ)) : G :=
  (r.map fun v => v.2 • base v.1).sum

theorem mapRow (φ : G →+ H) (base : I → G) (r : List (I × ℤ)) :
    evalRow (φ ∘ base) r = φ (evalRow base r) := by
  induction r with
  | nil => simp [evalRow]
  | cons v r ih =>
    simpa only [evalRow, List.map_cons, List.sum_cons, Function.comp_apply,
      map_add, map_zsmul] using congrArg (fun s => v.2 • φ (base v.1) + s) ih

/-- Row IDs, multiplicities and order are retained, including duplicates.
This is an identity on the matching lists, not just their lengths. -/
theorem sameMatches [DecidableEq G] [DecidableEq H] (φ : G →+ H)
    (inj : Function.Injective φ) (base : I → G) (q : G) (rows : List (List (I × ℤ))) :
    rows.filter (fun r => decide (evalRow (φ ∘ base) r = φ q)) =
    rows.filter (fun r => decide (evalRow base r = q)) := by
  simp only [mapRow, inj.eq_iff]

/-- The E1 public fixture and the tested degree-seven isogeny. -/
example : Nat.Coprime 2147505293 7 := by decide

end M31TransportedRows
