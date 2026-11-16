import TranscriptDeterminism

namespace XedniFirstCollisionLedger

/-- Every later live mass is bounded by the initial mass when each stage
partitions its entrants into continuations and first hits. -/
theorem live_le_initial (N : ℕ) (live firstHit : ℕ → ℕ)
    (hflow : ∀ k < N, live (k + 1) + firstHit k = live k) :
    ∀ k ≤ N, live k ≤ live 0 := by
  intro k hk
  induction k with
  | zero => exact le_refl _
  | succ k ih =>
      have hstep := hflow k (by omega)
      have hle : live (k + 1) ≤ live k := by omega
      exact hle.trans (ih (by omega))

/-- The first-hit buckets are disjoint: terminal live mass plus all first
hits equals the initial mass. -/
theorem first_hit_mass_identity (N : ℕ) (live firstHit : ℕ → ℕ)
    (hflow : ∀ k < N, live (k + 1) + firstHit k = live k) :
    live N + (∑ k ∈ Finset.range N, firstHit k) = live 0 := by
  induction N with
  | zero => simp
  | succ n ih =>
      have hprev : ∀ k < n, live (k + 1) + firstHit k = live k := by
        intro k hk
        exact hflow k (by omega)
      have hlast := hflow n (by omega)
      have hp := ih hprev
      rw [Finset.sum_range_succ]
      omega

/-- A uniform stage ratio bound, together with the stopping ledger,
bounds the total first-hit mass across any finite number of stages. -/
theorem first_hit_total_bound (N d c : ℕ) (live firstHit : ℕ → ℕ)
    (hflow : ∀ k < N, live (k + 1) + firstHit k = live k)
    (hstage : ∀ k < N, d * firstHit k ≤ c * live k) :
    d * (∑ k ∈ Finset.range N, firstHit k) ≤
      N * c * live 0 := by
  have hcap := live_le_initial N live firstHit hflow
  calc
    d * (∑ k ∈ Finset.range N, firstHit k) =
        ∑ k ∈ Finset.range N, d * firstHit k := by
          rw [Finset.mul_sum]
    _ ≤ ∑ k ∈ Finset.range N, c * live 0 := by
      apply Finset.sum_le_sum
      intro k hk
      have hkN : k < N := Finset.mem_range.mp hk
      exact (hstage k hkN).trans
        (Nat.mul_le_mul_left c (hcap k (by omega)))
    _ = N * c * live 0 := by simp [mul_assoc]

/-- Aggregate equal-weight transcript buckets. If every bucket has at
least `d` eligible scalars and at most `c` next-hit scalars, its encoding
mass satisfies the same ratio after summing over all bucket labels. -/
theorem uniform_bucket_count_bound {T F : Type*} [Fintype T]
    (d c : ℕ) (eligible nextHit : T → Finset F)
    (weight : T → ℕ)
    (hlive : ∀ t, d ≤ (eligible t).card)
    (hbad : ∀ t, (nextHit t).card ≤ c) :
    d * (∑ t : T, (nextHit t).card * weight t) ≤
      c * (∑ t : T, (eligible t).card * weight t) := by
  classical
  calc
    d * (∑ t : T, (nextHit t).card * weight t) =
        ∑ t : T, d * ((nextHit t).card * weight t) := by
          rw [Finset.mul_sum]
    _ ≤ ∑ t : T, c * ((eligible t).card * weight t) := by
      apply Finset.sum_le_sum
      intro t _
      have hcard : d * (nextHit t).card ≤ c * (eligible t).card := calc
        d * (nextHit t).card ≤ d * c := Nat.mul_le_mul_left d (hbad t)
        _ = c * d := by ac_rfl
        _ ≤ c * (eligible t).card := Nat.mul_le_mul_left c (hlive t)
      simpa [mul_assoc, mul_comm, mul_left_comm] using
        Nat.mul_le_mul_right (weight t) hcard
    _ = c * (∑ t : T, (eligible t).card * weight t) := by
      rw [Finset.mul_sum]

/-- If each of `m` stages has at most `m` next-hit scalar candidates per
live transcript and at least `q-m²` eligible scalars, the stopping ledger
gives the corresponding square-over-gap count bound. The node-to-stage
hypothesis is stated explicitly. -/
theorem conditional_square_over_gap (q m : ℕ)
    (live firstHit : ℕ → ℕ)
    (_hq : m * m < q)
    (hflow : ∀ k < m, live (k + 1) + firstHit k = live k)
    (hstage : ∀ k < m,
      (q - m * m) * firstHit k ≤ m * live k) :
    (q - m * m) * (∑ k ∈ Finset.range m, firstHit k) ≤
      m * m * live 0 := by
  exact first_hit_total_bound m (q - m * m) m live firstHit hflow hstage

#print axioms live_le_initial
#print axioms first_hit_mass_identity
#print axioms first_hit_total_bound
#print axioms uniform_bucket_count_bound
#print axioms conditional_square_over_gap

end XedniFirstCollisionLedger
