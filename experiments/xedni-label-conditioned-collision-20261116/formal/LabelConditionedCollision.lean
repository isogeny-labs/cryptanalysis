import RandomLabelCoupling
import SymbolicCollision

namespace XedniLabelConditionedCollision

open XedniRandomLabelCoupling XedniSymbolicCollision

/-- Number of bijective encodings that give a prescribed collision-free
visible label tuple for one target scalar. -/
noncomputable def fiberCount {F L : Type*} [Fintype F] [Fintype L]
    {n : ℕ} (trace : F → Fin n → F) (w : F) (labels : Fin n → L) : ℕ :=
  eventCount (trace w) (fun seen => seen = labels)

/-- Every eligible target scalar has the same encoding count for any fixed
collision-free visible label tuple. -/
theorem fiber_count_eq {F L : Type*} [Fintype F] [Fintype L]
    {n : ℕ} (trace : F → Fin n → F) (w₁ w₂ : F)
    (h₁ : Function.Injective (trace w₁))
    (h₂ : Function.Injective (trace w₂))
    (labels : Fin n → L) :
    fiberCount trace w₁ labels = fiberCount trace w₂ labels := by
  exact label_event_card_eq (trace w₁) (trace w₂) h₁ h₂
    (fun seen => seen = labels)

/-- On any fixed collision-free label fiber, the encoding mass of scalars
whose selected symbolic forms collide is bounded by the pair count times
the mass of one eligible scalar. The forms may depend on the visible labels. -/
theorem collision_fiber_mass_le {F L : Type*}
    [Fintype F] [Fintype L] [DecidableEq F] [Field F]
    {n m : ℕ} (trace : F → Fin n → F)
    (eligible : Finset F) (w₀ : F) (hw₀ : w₀ ∈ eligible)
    (hinj : ∀ w ∈ eligible, Function.Injective (trace w))
    (forms : (Fin n → L) → Fin m → Affine F)
    (labels : Fin n → L) :
    (∑ w ∈ eligible ∩ collisionSet (forms labels),
      fiberCount trace w labels) ≤
      m * m * fiberCount trace w₀ labels := by
  classical
  let bad := eligible ∩ collisionSet (forms labels)
  have hsum :
      (∑ w ∈ bad, fiberCount trace w labels) =
        bad.card * fiberCount trace w₀ labels := by
    calc
      (∑ w ∈ bad, fiberCount trace w labels) =
          ∑ w ∈ bad, fiberCount trace w₀ labels := by
        apply Finset.sum_congr rfl
        intro w hw
        exact fiber_count_eq trace w w₀
          (hinj w ((Finset.mem_inter.mp hw).1)) (hinj w₀ hw₀) labels
      _ = bad.card * fiberCount trace w₀ labels := by simp
  have hcard : bad.card ≤ m * m := by
    exact (Finset.card_le_card Finset.inter_subset_right).trans
      (symbolic_collision_bound (forms labels))
  change (∑ w ∈ bad, fiberCount trace w labels) ≤
    m * m * fiberCount trace w₀ labels
  rw [hsum]
  exact Nat.mul_le_mul_right _ hcard

#print axioms fiberCount
#print axioms fiber_count_eq
#print axioms collision_fiber_mass_le

end XedniLabelConditionedCollision
