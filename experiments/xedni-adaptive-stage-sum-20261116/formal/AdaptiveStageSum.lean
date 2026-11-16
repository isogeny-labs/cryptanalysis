import PrefixPatternBridge

namespace XedniAdaptiveStageSum

open XedniPrefixPatternBridge XedniSymbolicCollision XedniFirstCollisionLedger

/-- Executions whose first informative hit has not occurred before stage k.
A missing hit time stays live at every stage. -/
noncomputable def liveSet {Ω : Type*} [Fintype Ω]
    (first : Ω → Option ℕ) (k : ℕ) : Finset Ω := by
  classical
  exact Finset.univ.filter (fun ω =>
    match first ω with
    | none => True
    | some j => k ≤ j)

noncomputable def hitSet {Ω : Type*} [Fintype Ω]
    (first : Ω → Option ℕ) (k : ℕ) : Finset Ω := by
  classical
  exact Finset.univ.filter (fun ω => first ω = some k)

/-- Every live execution either continues or has its first hit now. -/
theorem live_step_partition {Ω : Type*} [Fintype Ω] [DecidableEq Ω]
    (first : Ω → Option ℕ) (k : ℕ) :
    liveSet first k = liveSet first (k+1) ∪ hitSet first k := by
  classical
  ext ω
  simp only [liveSet, hitSet, Finset.mem_filter, Finset.mem_univ,
    true_and, Finset.mem_union]
  cases h : first ω with
  | none => simp [h]
  | some j => simp [h]; omega

/-- Continuing and first-hit execution sets are disjoint. -/
theorem live_hit_disjoint {Ω : Type*} [Fintype Ω] [DecidableEq Ω]
    (first : Ω → Option ℕ) (k : ℕ) :
    Disjoint (liveSet first (k+1)) (hitSet first k) := by
  classical
  apply Finset.disjoint_left.mpr
  intro ω hLive hHit
  have heq : first ω = some k := by simpa [hitSet] using hHit
  have hle : k+1 ≤ k := by simpa [liveSet, heq] using hLive
  omega

/-- Conservation follows directly from first-hit time on the execution
space; no separate mass-flow premise is needed. -/
theorem stop_flow {Ω : Type*} [Fintype Ω] [DecidableEq Ω]
    (first : Ω → Option ℕ) (k : ℕ) :
    (liveSet first (k+1)).card + (hitSet first k).card =
      (liveSet first k).card := by
  classical
  rw [live_step_partition first k]
  exact (Finset.card_union_of_disjoint (live_hit_disjoint first k)).symm

/-- Total first-hit count plus survivors equals the execution-space size. -/
theorem stopped_mass_identity {Ω : Type*} [Fintype Ω] [DecidableEq Ω]
    (first : Ω → Option ℕ) (N : ℕ) :
    (liveSet first N).card +
      (∑ k ∈ Finset.range N, (hitSet first k).card) = Fintype.card Ω := by
  have h := first_hit_mass_identity N
    (fun k => (liveSet first k).card)
    (fun k => (hitSet first k).card)
    (by intro k _; exact stop_flow first k)
  have hzero : liveSet first 0 = Finset.univ := by
    ext ω
    simp only [liveSet, Finset.mem_filter, Finset.mem_univ, true_and]
    cases first ω <;> simp
  rw [hzero] at h
  simpa using h

/-- Sum the fixed-prefix weighted inequality across every visible bucket
at one stage. Each bucket may have its own forms and label tuple. -/
theorem stage_bucket_mass_bound {F L T : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L] [Fintype T]
    {n : ℕ} (forms : T → Fin n → Affine F)
    (newForm : T → Affine F) (labels : T → Fin n → L)
    (firstHit : T → Finset F)
    (hsubset : ∀ t, firstHit t ⊆
      eligible (forms t) ∩ nextCandidates (forms t) (newForm t)) :
    (Fintype.card F - n*n) *
      (∑ t : T, ∑ w ∈ firstHit t, prefixFiber (forms t) w (labels t)) ≤
    n * (∑ t : T, ∑ w ∈ eligible (forms t),
      prefixFiber (forms t) w (labels t)) := by
  classical
  rw [Finset.mul_sum, Finset.mul_sum]
  apply Finset.sum_le_sum
  intro t _
  exact weighted_first_hit_bound (forms t) (newForm t) (labels t)
    (firstHit t) (hsubset t)


/-- An aggregate first-hit bound for a finite execution space once each
stage's live and hit sets are exactly represented by its visible-prefix
fibers. The bucket identities are explicit structural obligations. -/
theorem aggregate_bucket_bound {F L T Ω : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L]
    [Fintype T] [Fintype Ω] [DecidableEq Ω]
    (N m : ℕ) (first : Ω → Option ℕ) (n : ℕ → ℕ)
    (forms : ∀ k, T → Fin (n k) → Affine F)
    (newForm : ∀ k, T → Affine F)
    (labels : ∀ k, T → Fin (n k) → L)
    (firstHit : ∀ k, T → Finset F)
    (hN : N ≤ m)
    (hn : ∀ k < N, n k ≤ m)
    (hsubset : ∀ k < N, ∀ t, firstHit k t ⊆
      eligible (forms k t) ∩ nextCandidates (forms k t) (newForm k t))
    (hLive : ∀ k < N, (liveSet first k).card =
      ∑ t : T, ∑ w ∈ eligible (forms k t),
        prefixFiber (forms k t) w (labels k t))
    (hHit : ∀ k < N, (hitSet first k).card =
      ∑ t : T, ∑ w ∈ firstHit k t,
        prefixFiber (forms k t) w (labels k t)) :
    (Fintype.card F - m*m) *
      (∑ k ∈ Finset.range N, (hitSet first k).card) ≤
    m*m * Fintype.card Ω := by
  classical
  have hstage : ∀ k < N,
      (Fintype.card F - m*m) * (hitSet first k).card ≤
      m * (liveSet first k).card := by
    intro k hk
    have hnk := hn k hk
    have hsq : n k * n k ≤ m*m := Nat.mul_le_mul hnk hnk
    have hsub : Fintype.card F - m*m ≤
        Fintype.card F - n k * n k := by omega
    have hfixed := stage_bucket_mass_bound (forms k) (newForm k)
      (labels k) (firstHit k) (hsubset k hk)
    rw [← hLive k hk, ← hHit k hk] at hfixed
    calc
      _ ≤ (Fintype.card F - n k * n k) *
          (hitSet first k).card := Nat.mul_le_mul_right _ hsub
      _ ≤ n k * (liveSet first k).card := hfixed
      _ ≤ m * (liveSet first k).card := Nat.mul_le_mul_right _ hnk
  have htotal := first_hit_total_bound N
    (Fintype.card F - m*m) m
    (fun k => (liveSet first k).card)
    (fun k => (hitSet first k).card)
    (by intro k _; exact stop_flow first k)
    hstage
  have hzero : (liveSet first 0).card = Fintype.card Ω := by
    have h := stopped_mass_identity first 0
    simpa using h
  rw [hzero] at htotal
  calc
    _ ≤ N*m*Fintype.card Ω := htotal
    _ ≤ m*m*Fintype.card Ω := by
      exact Nat.mul_le_mul_right _ (Nat.mul_le_mul_right m hN)

#print axioms aggregate_bucket_bound
#print axioms liveSet
#print axioms hitSet
#print axioms live_step_partition
#print axioms live_hit_disjoint
#print axioms stop_flow
#print axioms stopped_mass_identity
#print axioms stage_bucket_mass_bound

end XedniAdaptiveStageSum
