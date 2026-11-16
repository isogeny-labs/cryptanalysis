import GroupFiberBound

namespace XedniAdaptiveTotalBound

open XedniBucketFiberPartition XedniGroupFiberBound
open XedniSymbolicCollision XedniFirstHitPartition
open XedniTypedPrefixProgram XedniStageHitEquivalence
open XedniAdaptiveProgramInvariant XedniAdaptiveStageSum
open XedniPrefixPatternBridge

/-- A bucket mass is the sum of its exact encoding fibers over the
accepted scalars in each visible bucket. -/
theorem bucketMass_eq_fiber_sum {W E T : Type*}
    [Fintype W] [Fintype E] [Fintype T]
    (bucket : W → E → T) (accepted : T → Finset W) :
    bucketMass bucket (fun t w => w ∈ accepted t) =
      ∑ t : T, ∑ w ∈ accepted t, encodingFiber bucket w t := by
  classical
  unfold bucketMass
  rw [Fintype.sum_prod_type]
  simp only [Fintype.card_eq_nat_card]
  apply Finset.sum_congr rfl
  intro t _
  calc
    (∑ w : W, Nat.card
      {e : E // w ∈ accepted t ∧ bucket w e = t}) =
      ∑ w : W, if w ∈ accepted t then encodingFiber bucket w t else 0 := by
        apply Finset.sum_congr rfl
        intro w _
        by_cases hw : w ∈ accepted t
        · simp only [hw, true_and, ite_true]
          unfold encodingFiber
          simp only [Fintype.card_eq_nat_card]
        · simp [hw]
    _ = ∑ w ∈ accepted t, encodingFiber bucket w t := by simp

/-- The pointwise weighted bound sums across every visible bucket. -/
theorem summed_fiber_bound {W E T : Type*}
    [Fintype W] [DecidableEq W] [Fintype E] [Fintype T]
    (bucket : W → E → T) (eligible candidates : T → Finset W)
    (a b : ℕ)
    (hbound : ∀ t : T,
      a * (∑ w ∈ eligible t ∩ candidates t,
        encodingFiber bucket w t) ≤
      b * (∑ w ∈ eligible t,
        encodingFiber bucket w t)) :
    a * bucketMass bucket
      (fun t w => w ∈ eligible t ∩ candidates t) ≤
    b * bucketMass bucket (fun t w => w ∈ eligible t) := by
  rw [bucketMass_eq_fiber_sum, bucketMass_eq_fiber_sum]
  calc
    a * (∑ t : T, ∑ w ∈ eligible t ∩ candidates t,
      encodingFiber bucket w t) =
        ∑ t : T, a * (∑ w ∈ eligible t ∩ candidates t,
          encodingFiber bucket w t) := Finset.mul_sum _ _ _
    _ ≤ ∑ t : T, b * (∑ w ∈ eligible t,
      encodingFiber bucket w t) :=
        Finset.sum_le_sum (fun t _ => hbound t)
    _ = b * (∑ t : T, ∑ w ∈ eligible t,
      encodingFiber bucket w t) := (Finset.mul_sum _ _ _).symm

/-- In any finite label-adaptive group program, the actual first-hit
executions at stage `k` obey the weighted candidate bound relative to
executions still live at that stage. -/
theorem execution_stage_weighted_bound {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (h2 : 2 ≤ k) (hk : k < m) (fallback : L) :
    (Fintype.card F - k * k) *
      (hitSet (firstHit (executionHit (F := F) program G)) k).card ≤
    k * (liveSet (firstHit (executionHit (F := F) program G)) k).card := by
  classical
  let hk' : k ≤ m := Nat.le_of_lt hk
  let fs (labels : Fin k → L) :=
    formsInBucket (F := F) program h2 hk' labels
  let ns (labels : Fin k → L) :=
    nextFormInBucket (F := F) program hk fallback labels
  have hbound (labels : Fin k → L) :
      (Fintype.card F - k * k) *
        (∑ w ∈ eligible (fs labels) ∩ nextCandidates (fs labels) (ns labels),
          encodingFiber (executionPrefixBucket (F := F) program G hk') w labels) ≤
      k * (∑ w ∈ eligible (fs labels),
        encodingFiber (executionPrefixBucket (F := F) program G hk') w labels) := by
    have h := weighted_group_next_candidate_bound G hinj
      (fs labels) (ns labels) labels
    simp_rw [adaptive_encoding_fiber_eq_group_fiber program G h2 hk']
    exact h
  have hsum := summed_fiber_bound
    (executionPrefixBucket (F := F) program G hk')
    (fun labels => eligible (fs labels))
    (fun labels => nextCandidates (fs labels) (ns labels))
    (Fintype.card F - k * k) k hbound
  rw [execution_hit_card_eq_bucket_mass program G hinj h2 hk fallback,
    execution_live_card_eq_bucket_mass program G hinj h2 hk']
  simpa only [fs, ns, hk'] using hsum

/-- All first informative hits after the two seed points, summed over
the program's remaining stages, obey a quadratic-over-field bound. -/
theorem execution_late_total_bound {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (fallback : L) :
    (Fintype.card F - m * m) *
      (∑ k ∈ Finset.Ico 2 m,
        (hitSet (firstHit (executionHit (F := F) program G)) k).card) ≤
    m * m * Fintype.card (F × (A ≃ L)) := by
  classical
  let first := firstHit (executionHit (F := F) program G)
  have hstage (k : ℕ) (hk : k ∈ Finset.Ico 2 m) :
      (Fintype.card F - m * m) * (hitSet first k).card ≤
      m * Fintype.card (F × (A ≃ L)) := by
    have h2 : 2 ≤ k := (Finset.mem_Ico.mp hk).1
    have hkm : k < m := (Finset.mem_Ico.mp hk).2
    have hsq : k * k ≤ m * m := Nat.mul_le_mul (Nat.le_of_lt hkm) (Nat.le_of_lt hkm)
    have hsub : Fintype.card F - m * m ≤ Fintype.card F - k * k := by omega
    have hfixed := execution_stage_weighted_bound program G hinj h2 hkm fallback
    have hlive : (liveSet first k).card ≤ Fintype.card (F × (A ≃ L)) := by
      simpa only [Fintype.card_coe, Finset.card_univ] using
        (Finset.card_le_card (Finset.subset_univ (liveSet first k)))
    calc
      _ ≤ (Fintype.card F - k * k) * (hitSet first k).card :=
        Nat.mul_le_mul_right _ hsub
      _ ≤ k * (liveSet first k).card := hfixed
      _ ≤ m * (liveSet first k).card :=
        Nat.mul_le_mul_right _ (Nat.le_of_lt hkm)
      _ ≤ m * Fintype.card (F × (A ≃ L)) := Nat.mul_le_mul_left _ hlive
  calc
    (Fintype.card F - m * m) *
        (∑ k ∈ Finset.Ico 2 m, (hitSet first k).card) =
      ∑ k ∈ Finset.Ico 2 m,
        (Fintype.card F - m * m) * (hitSet first k).card :=
          Finset.mul_sum _ _ _
    _ ≤ ∑ k ∈ Finset.Ico 2 m,
        m * Fintype.card (F × (A ≃ L)) :=
          Finset.sum_le_sum (fun k hk => hstage k hk)
    _ = (Finset.Ico 2 m).card *
        (m * Fintype.card (F × (A ≃ L))) := by simp
    _ ≤ m * (m * Fintype.card (F × (A ≃ L))) := by
      apply Nat.mul_le_mul_right
      simp only [Nat.card_Ico]
      omega
    _ = m * m * Fintype.card (F × (A ≃ L)) := by ring

#print axioms bucketMass_eq_fiber_sum
#print axioms summed_fiber_bound
#print axioms execution_stage_weighted_bound
#print axioms execution_late_total_bound

end XedniAdaptiveTotalBound
