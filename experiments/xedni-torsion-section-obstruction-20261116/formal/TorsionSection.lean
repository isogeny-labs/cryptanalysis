import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniTorsionSection

variable {H C : Type*} [AddCommGroup H] [AddCommGroup C]

/-- A public torsion relation cannot lift through a reduction map into a group
with no corresponding torsion, regardless of how the lift is selected. -/
theorem torsion_relation_fails (q : ℕ) (c : C) (hc0 : c ≠ 0)
    (reduction : H →+ C) (hfree : ∀ h : H, q • h = 0 → h = 0)
    (lift : C → H) (hright : ∀ x : C, reduction (lift x) = x) :
    q • lift c ≠ 0 := by
  intro hq
  have hz : lift c = 0 := hfree (lift c) hq
  apply hc0
  calc
    c = reduction (lift c) := (hright c).symm
    _ = 0 := by rw [hz]; simp

/-- No additive section of reduction can cover a nonzero q-torsion point if
the lift group has no nonzero q-torsion. -/
theorem no_additive_section (q : ℕ) (c : C) (hc : q • c = 0) (hc0 : c ≠ 0)
    (reduction : H →+ C) (hfree : ∀ h : H, q • h = 0 → h = 0)
    (sec : C →+ H) (hright : ∀ x : C, reduction (sec x) = x) :
    False := by
  have hq : q • sec c = 0 := by
    calc
      q • sec c = sec (q • c) := by simp
      _ = 0 := by rw [hc]; simp
  exact (torsion_relation_fails q c hc0 reduction hfree sec hright) hq

/-- A set-theoretic right inverse cannot preserve even the single relation
`q • c = 0` at a nonzero public q-torsion point. -/
theorem no_relation_preserving_lift (q : ℕ) (c : C)
    (hc : q • c = 0) (hc0 : c ≠ 0)
    (reduction : H →+ C) (hfree : ∀ h : H, q • h = 0 → h = 0)
    (lift : C → H) (hright : ∀ x : C, reduction (lift x) = x)
    (hpreserves : q • c = 0 → q • lift c = 0) : False := by
  exact (torsion_relation_fails q c hc0 reduction hfree lift hright) (hpreserves hc)

/-- The explicit cyclic-target specialization. Here `1` has the public
relation `q • 1 = 0`, which a right inverse cannot preserve. -/
theorem zmod_no_relation_preserving_lift (q : ℕ) (hq : 1 < q) [NeZero q]
    (reduction : H →+ ZMod q) (hfree : ∀ h : H, q • h = 0 → h = 0)
    (lift : ZMod q → H) (hright : ∀ x : ZMod q, reduction (lift x) = x)
    (hpreserves : q • (1 : ZMod q) = 0 → q • lift 1 = 0) : False := by
  have htor : q • (1 : ZMod q) = 0 := by
    simp [nsmul_eq_mul]
  have hone : (1 : ZMod q) ≠ 0 := by
    rw [Ne, ZMod.one_eq_zero_iff]
    omega
  exact no_relation_preserving_lift q (1 : ZMod q) htor hone
    reduction hfree lift hright hpreserves

/-- The failure of a set-theoretic lift to commute with multiplication by `q`. -/
def torsionDefect (q : ℕ) (lift : C → H) (c : C) : H :=
  q • lift c - lift (q • c)

/-- For a rational lift with no `q`-torsion, the defect at a nonzero public
`q`-torsion point is nonzero whenever zero lifts to zero. -/
theorem torsion_defect_nonzero (q : ℕ) (c : C)
    (hc : q • c = 0) (hc0 : c ≠ 0)
    (reduction : H →+ C) (hfree : ∀ h : H, q • h = 0 → h = 0)
    (lift : C → H) (hright : ∀ x : C, reduction (lift x) = x)
    (hzero : lift 0 = 0) :
    torsionDefect q lift c ≠ 0 := by
  simpa [torsionDefect, hc, hzero] using
    (torsion_relation_fails q c hc0 reduction hfree lift hright)

/-- Any additive map from a `q`-torsion point to a characteristic-zero field
vanishes on that point. -/
theorem additive_log_kills_torsion {K : Type*} [Field K] [CharZero K]
    (q : ℕ) (hq : 0 < q) (c : C) (hc : q • c = 0)
    (log : C →+ K) : log c = 0 := by
  have hqlog : q • log c = 0 := by
    calc
      q • log c = log (q • c) := by simp
      _ = 0 := by rw [hc]; simp
  have hqcast : (q : K) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hq)
  apply (mul_eq_zero.mp ?_).resolve_left hqcast
  simpa [nsmul_eq_mul] using hqlog

/-- A homomorphic lift followed by an additive logarithm has zero output on
every point of a finite-order public subgroup. -/
theorem lifted_additive_log_zero {K : Type*} [Field K] [CharZero K]
    (q : ℕ) (hq : 0 < q) (c : C) (hc : q • c = 0)
    (sectionHom : C →+ H) (log : H →+ K) :
    log (sectionHom c) = 0 := by
  exact additive_log_kills_torsion q hq c hc (log.comp sectionHom)

#print axioms torsion_relation_fails
#print axioms no_additive_section
#print axioms no_relation_preserving_lift
#print axioms zmod_no_relation_preserving_lift
#print axioms torsion_defect_nonzero
#print axioms additive_log_kills_torsion
#print axioms lifted_additive_log_zero

end XedniTorsionSection
