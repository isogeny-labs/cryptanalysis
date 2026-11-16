import RandomLabelCoupling
import Mathlib.Data.Fin.Tuple.Basic

namespace XedniRandomLabelOracleStep

open XedniRandomLabelCoupling

/-- Appending one group element outside the prior trace preserves
injectivity. -/
theorem fresh_snoc_injective {G : Type*} {n : ℕ}
    (x : Fin n → G) (xNew : G)
    (hx : Function.Injective x) (hfresh : xNew ∉ Set.range x) :
    Function.Injective (Fin.snoc x xNew) := by
  exact Fin.snoc_injective_iff.mpr ⟨hx, hfresh⟩

/-- One fresh oracle result extends the random-label coupling. The paired
encoding preserves every old visible label and gives the same label to the
new output. -/
theorem fresh_oracle_step_coupling {G L : Type*} {n : ℕ}
    (x y : Fin n → G) (xNew yNew : G)
    (hx : Function.Injective x) (hy : Function.Injective y)
    (hxfresh : xNew ∉ Set.range x) (hyfresh : yNew ∉ Set.range y) :
    ∃ Φ : (G ≃ L) ≃ (G ≃ L),
      (∀ (enc : G ≃ L) (i : Fin n), (Φ enc) (y i) = enc (x i)) ∧
      (∀ (enc : G ≃ L), (Φ enc) yNew = enc xNew) := by
  have hx' := fresh_snoc_injective x xNew hx hxfresh
  have hy' := fresh_snoc_injective y yNew hy hyfresh
  obtain ⟨Φ, hΦ⟩ := injective_trace_label_coupling
    (Fin.snoc x xNew) (Fin.snoc y yNew) hx' hy'
  refine ⟨Φ, ?_, ?_⟩
  · intro enc i
    simpa only [Fin.snoc_castSucc] using hΦ enc i.castSucc
  · intro enc
    simpa only [Fin.snoc_last] using hΦ enc (Fin.last n)

/-- The full old-plus-new label tuple has the same event counts after one
fresh oracle output. -/
theorem fresh_oracle_step_event_count {G L : Type*}
    [Fintype G] [Fintype L] {n : ℕ}
    (x y : Fin n → G) (xNew yNew : G)
    (hx : Function.Injective x) (hy : Function.Injective y)
    (hxfresh : xNew ∉ Set.range x) (hyfresh : yNew ∉ Set.range y)
    (event : (Fin (n + 1) → L) → Prop) :
    eventCount (Fin.snoc x xNew) event =
      eventCount (Fin.snoc y yNew) event := by
  exact label_event_card_eq
    (Fin.snoc x xNew) (Fin.snoc y yNew)
    (fresh_snoc_injective x xNew hx hxfresh)
    (fresh_snoc_injective y yNew hy hyfresh) event

/-- If the next oracle command adds the same two previously observed
indices in each execution, the fresh-result coupling applies to the actual
group-operation outputs. -/
theorem fresh_add_oracle_step {G L : Type*} [Add G] {n : ℕ}
    (x y : Fin n → G) (i j : Fin n)
    (hx : Function.Injective x) (hy : Function.Injective y)
    (hxfresh : x i + x j ∉ Set.range x)
    (hyfresh : y i + y j ∉ Set.range y) :
    ∃ Φ : (G ≃ L) ≃ (G ≃ L),
      (∀ (enc : G ≃ L) (k : Fin n), (Φ enc) (y k) = enc (x k)) ∧
      (∀ (enc : G ≃ L),
        (Φ enc) (y i + y j) = enc (x i + x j)) := by
  exact fresh_oracle_step_coupling x y
    (x i + x j) (y i + y j) hx hy hxfresh hyfresh

#print axioms fresh_snoc_injective
#print axioms fresh_oracle_step_coupling
#print axioms fresh_oracle_step_event_count
#print axioms fresh_add_oracle_step

end XedniRandomLabelOracleStep
