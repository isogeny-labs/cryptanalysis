import OracleStep

namespace XedniAdaptiveOracleCoupling

open XedniRandomLabelCoupling XedniRandomLabelOracleStep

/-- Count encodings for which an adaptive label-based command chooses a
specified pair, the group output is fresh, and the complete visible label
tuple satisfies an event. -/
noncomputable def branchCount {G L : Type*} [Fintype G] [Fintype L]
    [Add G] {n : ℕ} (x : Fin n → G)
    (choose : (Fin n → L) → Fin n × Fin n)
    (ij : Fin n × Fin n) (event : (Fin (n + 1) → L) → Prop) : ℕ := by
  classical
  exact eventCount (Fin.snoc x (x ij.1 + x ij.2))
    (fun labels =>
      choose (fun k => labels k.castSucc) = ij ∧ event labels)

/-- Adaptive branch selection leaves the fresh-output label event count
unchanged between two injective group traces. The decision may inspect the
entire previous visible label tuple. -/
theorem fresh_branch_count_eq {G L : Type*} [Fintype G] [Fintype L]
    [Add G] {n : ℕ} (x y : Fin n → G)
    (hx : Function.Injective x) (hy : Function.Injective y)
    (choose : (Fin n → L) → Fin n × Fin n)
    (ij : Fin n × Fin n)
    (hxfresh : x ij.1 + x ij.2 ∉ Set.range x)
    (hyfresh : y ij.1 + y ij.2 ∉ Set.range y)
    (event : (Fin (n + 1) → L) → Prop) :
    branchCount x choose ij event = branchCount y choose ij event := by
  exact fresh_oracle_step_event_count x y
    (x ij.1 + x ij.2) (y ij.1 + y ij.2)
    hx hy hxfresh hyfresh
    (fun labels => choose (fun k => labels k.castSucc) = ij ∧ event labels)

/-- Sum over every possible command branch. Under freshness for every
command that can be chosen, the complete next-label event has equal counts
for the two input scalars. -/
theorem adaptive_fresh_event_count_eq {G L : Type*}
    [Fintype G] [Fintype L] [Add G] {n : ℕ}
    (x y : Fin n → G)
    (hx : Function.Injective x) (hy : Function.Injective y)
    (choose : (Fin n → L) → Fin n × Fin n)
    (allowed : Finset (Fin n × Fin n))
    (_hchoose : ∀ labels, choose labels ∈ allowed)
    (hxfresh : ∀ ij ∈ allowed, x ij.1 + x ij.2 ∉ Set.range x)
    (hyfresh : ∀ ij ∈ allowed, y ij.1 + y ij.2 ∉ Set.range y)
    (event : (Fin (n + 1) → L) → Prop) :
    (∑ ij ∈ allowed, branchCount x choose ij event) =
      ∑ ij ∈ allowed, branchCount y choose ij event := by
  classical
  apply Finset.sum_congr rfl
  intro ij hij
  exact fresh_branch_count_eq x y hx hy choose ij
    (hxfresh ij hij) (hyfresh ij hij) event

#print axioms branchCount
#print axioms fresh_branch_count_eq
#print axioms adaptive_fresh_event_count_eq

end XedniAdaptiveOracleCoupling
