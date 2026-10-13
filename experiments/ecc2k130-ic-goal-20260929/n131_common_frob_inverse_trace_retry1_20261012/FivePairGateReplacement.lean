import Std

/-! Exact source-gate substitution for five point-pair blocks.  The concrete
field and curve enter through the source equivalence, distinct-column rule,
and point-sum map. -/
namespace FivePairGateReplacement

universe u v
variable {Code : Type u} {Target : Type v}

def HasRelation (gate : Code → Prop)
    (distinctColumns : (Fin 5 → Fin 2 → Code) → Prop)
    (pointSum : (Fin 5 → Fin 2 → Code) → Target) (target : Target) : Prop :=
  ∃ codes : Fin 5 → Fin 2 → Code,
    (∀ i j, gate (codes i j)) ∧ distinctColumns codes ∧ pointSum codes = target

theorem exact_gate_substitution
    (bdd inverseTrace : Code → Prop)
    (distinctColumns : (Fin 5 → Fin 2 → Code) → Prop)
    (pointSum : (Fin 5 → Fin 2 → Code) → Target) (target : Target)
    (sameSource : ∀ code, bdd code ↔ inverseTrace code) :
    HasRelation bdd distinctColumns pointSum target ↔
      HasRelation inverseTrace distinctColumns pointSum target := by
  constructor
  · rintro ⟨codes, hgate, hdistinct, hsum⟩
    exact ⟨codes, (fun i j => (sameSource (codes i j)).mp (hgate i j)),
      hdistinct, hsum⟩
  · rintro ⟨codes, hgate, hdistinct, hsum⟩
    exact ⟨codes, (fun i j => (sameSource (codes i j)).mpr (hgate i j)),
      hdistinct, hsum⟩

#print axioms FivePairGateReplacement.exact_gate_substitution

end FivePairGateReplacement
