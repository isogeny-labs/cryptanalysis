import TerminalSeparation

namespace M31PeriodicCover
open M31TerminalSeparation M31ArchiveData M31ArchiveRoots

def labels (d : Nat) : Finset Nat := (archived.map (fun q => label d q.1)).toFinset

theorem labels_succ (d : Nat) : labels (d+1) = (labels d).image step := by
  ext t
  simp only [labels, List.mem_toFinset, List.mem_map, Finset.mem_image]
  constructor
  · rintro ⟨q,hq,rfl⟩
    exact ⟨label d q.1, ⟨q,hq,rfl⟩, (Function.iterate_succ_apply' step d q.1).symm⟩
  · rintro ⟨_, ⟨q,hq,rfl⟩,rfl⟩
    exact ⟨q,hq,Function.iterate_succ_apply' step d q.1⟩

theorem monotone_loss : Antitone (fun d => (labels d).card) := by
  apply antitone_nat_of_succ_le
  intro d
  rw [labels_succ]
  exact Finset.card_image_le

set_option maxRecDepth 32768 in
theorem returns : ∀ q ∈ archived, label 61 q.1 = label 31 q.1 := by decide +kernel

theorem labels_return : labels 61 = labels 31 := by
  unfold labels
  rw [List.map_congr_left returns]

theorem periodic (k : Nat) : labels (31+k+30) = labels (31+k) := by
  induction k with
  | zero => exact labels_return
  | succ k ih =>
    rw [show 31+(k+1)+30 = (31+k+30)+1 by omega, labels_succ, ih]
    exact (labels_succ (31+k)).symm

set_option maxRecDepth 32768 in
theorem size31 : (labels 31).card = 11 := by decide +kernel

theorem stable (k : Nat) : (labels (31+k)).card = 11 := by
  induction k using Nat.strong_induction_on with
  | h k ih =>
    by_cases small : k ≤ 30
    · have lower := monotone_loss (show 31+k ≤ 61 by omega)
      have upper := monotone_loss (show 31 ≤ 31+k by omega)
      dsimp only at lower upper
      rw [labels_return, size31] at lower
      rw [size31] at upper
      exact Nat.le_antisymm upper lower
    · have recur := periodic (k-30)
      rw [show 31+(k-30)+30 = 31+k by omega] at recur
      rw [recur]
      exact ih (k-30) (by omega)

theorem first_stable_depth (d : Nat) : (labels d).card = 11 ↔ 31 ≤ d := by
  constructor
  · intro eq
    by_contra early
    have bound := monotone_loss (show d ≤ 30 by omega)
    change (labels 30).card ≤ (labels d).card at bound
    have size30 : (labels 30).card = 12 := by decide +kernel
    omega
  · intro hd
    simpa only [show 31 + (d-31) = d by omega] using stable (d-31)

theorem lower_bound (d : Nat) : 11 ≤ (labels d).card := by
  by_cases h : d ≤ 31
  · have bound := monotone_loss h
    simpa only [size31] using bound
  · have result := stable (d-31)
    rw [show 31+(d-31) = d by omega] at result
    exact result.ge

theorem orbit_period {q : Nat × Nat} (hq : q ∈ archived) (d : Nat) :
    label (31+d+30) q.1 = label (31+d) q.1 := by
  have h := congrArg (step^[d]) (returns q hq)
  unfold label at *
  simpa only [← Function.iterate_add_apply, show d+61=31+d+30 by omega,
    show d+31=31+d by omega] using h

theorem phase {q : Nat × Nat} (hq : q ∈ archived) (d : Nat) :
    ∃ r : Fin 30, label (31+d) q.1 = label (31+r.val) q.1 := by
  induction d using Nat.strong_induction_on with
  | h d ih =>
    by_cases hd : d < 30
    · exact ⟨⟨d,hd⟩,rfl⟩
    · obtain ⟨r,hr⟩ := ih (d-30) (by omega)
      have back := orbit_period hq (d-30)
      rw [show 31+(d-30)+30 = 31+d by omega] at back
      exact ⟨r,back.trans hr⟩

set_option maxHeartbeats 8000000 in
set_option maxRecDepth 32768 in
theorem separate_cycles : ∀ x ∈ archived, ∀ y ∈ archived, ∀ r : Fin 30,
    label 31 x.1 = label (31+r.val) y.1 → label 31 x.1 = label 31 y.1 := by decide +kernel

theorem variable_depth {x y : Nat × Nat} (hx : x ∈ archived) (hy : y ∈ archived)
    (i j : Nat) (meet : label i x.1 = label j y.1) : label 31 x.1 = label 31 y.1 := by
  have full (n : Nat) : label (31+30*n) x.1 = label 31 x.1 := by
    induction n with
    | zero => rfl
    | succ n ih =>
      rw [show 31+30*(n+1)=31+30*n+30 by omega, orbit_period hx, ih]
  have move := congrArg (step^[31+29*i]) meet
  change step^[31+29*i] (step^[i] x.1) = step^[31+29*i] (step^[j] y.1) at move
  rw [← Function.iterate_add_apply, ← Function.iterate_add_apply] at move
  change label (31+29*i+i) x.1 = label (31+29*i+j) y.1 at move
  rw [show 31+29*i+i=31+30*i by omega, full, Nat.add_assoc] at move
  obtain ⟨r,hr⟩ := phase hy (29*i+j)
  exact separate_cycles x hx y hy r (move.trans hr)

end M31PeriodicCover
