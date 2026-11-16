import LabelConditionedCollision

namespace XedniGroupTraceInvariant

open XedniRandomLabelCoupling XedniSymbolicCollision

/-- A prior group-oracle trace whose entries are explicitly evaluated
symbolic affine forms. -/
def groupTrace {F A : Type*} [Field F] [AddCommGroup A] [Module F A]
    {n : ℕ} (G : A) (prior : Fin n → Affine F) (w : F) (i : Fin n) : A :=
  (eval (prior i) w) • G

/-- A group hit on a new, symbolically distinct form has unequal slopes
and identifies an informative affine collision. -/
theorem next_group_hit_informative {F A : Type*}
    [Field F] [AddCommGroup A] [Module F A]
    {n : ℕ} (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (prior : Fin n → Affine F) (next : Affine F)
    (hnew : ∀ i, prior i ≠ next) (w : F)
    (hhit : ∃ i, (eval next w) • G = groupTrace G prior w i) :
    ∃ i, (prior i).slope ≠ next.slope ∧
      eval (prior i) w = eval next w := by
  obtain ⟨i, hi⟩ := hhit
  have heq : eval (prior i) w = eval next w := hinj hi.symm
  have hs : (prior i).slope ≠ next.slope := by
    intro hs
    exact (same_slope_distinct_ne (prior i) next hs (hnew i) w) heq
  exact ⟨i, hs, heq⟩

/-- The actual group hit lies in the symbolic collision set for the
old forms followed by the label-selected new form. -/
theorem next_group_hit_mem_collision_set {F A : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A]
    {n : ℕ} (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (prior : Fin n → Affine F) (next : Affine F)
    (hnew : ∀ i, prior i ≠ next) (w : F)
    (hhit : ∃ i, (eval next w) • G = groupTrace G prior w i) :
    w ∈ collisionSet (Fin.snoc prior next) := by
  classical
  obtain ⟨i, hs, heq⟩ := next_group_hit_informative G hinj prior next hnew w hhit
  rw [collision_set_eq_candidates]
  let pair : Fin (n + 1) × Fin (n + 1) := (i.castSucc, Fin.last n)
  have hp : pair ∈ activePairs (Fin.snoc prior next) := by
    simp [pair, activePairs, Fin.snoc_castSucc, Fin.snoc_last,
      Fin.castSucc_lt_last, hs]
  have hc : w = candidate (prior i) next :=
    (unequal_slope_eq_iff_candidate (prior i) next hs w).mp heq
  refine Finset.mem_image.mpr ⟨pair, hp, ?_⟩
  simpa [pair, Fin.snoc_castSucc, Fin.snoc_last] using hc.symm

/-- Encodings that show one prescribed old-label tuple for a target scalar
on an actual group trace. -/
noncomputable def groupFiberCount {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A]
    [Fintype A] [Fintype L] {n : ℕ}
    (G : A) (prior : Fin n → Affine F) (w : F)
    (labels : Fin n → L) : ℕ :=
  eventCount (groupTrace G prior w) (fun seen => seen = labels)

/-- Eligible target scalars for which the selected next group output
matches an old group element. -/
noncomputable def actualGroupHits {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (eligible : Finset F) (prior : Fin n → Affine F)
    (next : (Fin n → L) → Affine F) (labels : Fin n → L) : Finset F := by
  classical
  exact eligible.filter (fun w =>
    ∃ i, (eval (next labels) w) • G = groupTrace G prior w i)

/-- On a fixed collision-free visible-label fiber, actual group-oracle
hits have at most the symbolic pair-bound encoding mass. -/
theorem actual_group_hit_fiber_mass_le {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A]
    [Fintype A] [Fintype L] {n : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (eligible : Finset F) (w₀ : F) (hw₀ : w₀ ∈ eligible)
    (prior : Fin n → Affine F)
    (next : (Fin n → L) → Affine F) (labels : Fin n → L)
    (hnew : ∀ i, prior i ≠ next labels)
    (htrace : ∀ w ∈ eligible, Function.Injective (groupTrace G prior w)) :
    (∑ w ∈ actualGroupHits G eligible prior next labels,
      groupFiberCount G prior w labels) ≤
      (n + 1) * (n + 1) * groupFiberCount G prior w₀ labels := by
  classical
  let bad := actualGroupHits G eligible prior next labels
  have hsum :
      (∑ w ∈ bad, groupFiberCount G prior w labels) =
        bad.card * groupFiberCount G prior w₀ labels := by
    calc
      (∑ w ∈ bad, groupFiberCount G prior w labels) =
          ∑ w ∈ bad, groupFiberCount G prior w₀ labels := by
        apply Finset.sum_congr rfl
        intro w hw
        exact label_event_card_eq (groupTrace G prior w)
          (groupTrace G prior w₀)
          (htrace w (Finset.mem_filter.mp hw).1)
          (htrace w₀ hw₀) (fun seen => seen = labels)
      _ = bad.card * groupFiberCount G prior w₀ labels := by simp
  have hsubset : bad ⊆ collisionSet (Fin.snoc prior (next labels)) := by
    intro w hw
    exact next_group_hit_mem_collision_set G hinj prior (next labels)
      hnew w (Finset.mem_filter.mp hw).2
  have hcard : bad.card ≤ (n + 1) * (n + 1) :=
    (Finset.card_le_card hsubset).trans
      (symbolic_collision_bound (Fin.snoc prior (next labels)))
  change (∑ w ∈ bad, groupFiberCount G prior w labels) ≤
    (n + 1) * (n + 1) * groupFiberCount G prior w₀ labels
  rw [hsum]
  exact Nat.mul_le_mul_right _ hcard

#print axioms groupTrace
#print axioms next_group_hit_informative
#print axioms next_group_hit_mem_collision_set
#print axioms groupFiberCount
#print axioms actualGroupHits
#print axioms actual_group_hit_fiber_mass_le

end XedniGroupTraceInvariant
