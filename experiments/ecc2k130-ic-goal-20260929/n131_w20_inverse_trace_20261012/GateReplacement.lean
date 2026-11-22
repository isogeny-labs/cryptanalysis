import Std

/-! Pointwise replacement of an exact source gate preserves seven-slot
relation witnesses, including the distinct-column constraint. -/
namespace W20GateReplacement

universe u v
variable {Code : Type u} {Target : Type v}

def HasRelation (gate : Code → Prop)
    (distinctColumns : (Fin 7 → Code) → Prop)
    (pointSum : (Fin 7 → Code) → Target) (target : Target) : Prop :=
  ∃ codes : Fin 7 → Code,
    (∀ i, gate (codes i)) ∧ distinctColumns codes ∧ pointSum codes = target

theorem exact_gate_substitution
    (bdd inverseTrace : Code → Prop)
    (distinctColumns : (Fin 7 → Code) → Prop)
    (pointSum : (Fin 7 → Code) → Target) (target : Target)
    (sameSource : ∀ code, bdd code ↔ inverseTrace code) :
    HasRelation bdd distinctColumns pointSum target ↔
      HasRelation inverseTrace distinctColumns pointSum target := by
  constructor
  · rintro ⟨codes, hgate, hdistinct, hsum⟩
    exact ⟨codes, (fun i => (sameSource (codes i)).mp (hgate i)),
      hdistinct, hsum⟩
  · rintro ⟨codes, hgate, hdistinct, hsum⟩
    exact ⟨codes, (fun i => (sameSource (codes i)).mpr (hgate i)),
      hdistinct, hsum⟩

#print axioms W20GateReplacement.exact_gate_substitution

end W20GateReplacement
