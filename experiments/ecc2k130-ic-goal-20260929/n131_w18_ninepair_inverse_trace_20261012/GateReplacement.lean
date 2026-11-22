import Std

/-! Replacing an exact source predicate preserves nine-pair relation witnesses.
The point-sum and distinct-column predicates are parameters, so the theorem
applies to the frozen curve once the two concrete source gates are shown equal. -/
namespace GateReplacement

universe u v
variable {Code : Type u} {Target : Type v}

def HasRelation (gate : Code → Prop)
    (distinctColumns : (Fin 9 → Code) → Prop)
    (pointSum : (Fin 9 → Code) → Target) (target : Target) : Prop :=
  ∃ codes : Fin 9 → Code,
    (∀ i, gate (codes i)) ∧ distinctColumns codes ∧ pointSum codes = target

theorem exact_gate_substitution
    (bdd inverseTrace : Code → Prop)
    (distinctColumns : (Fin 9 → Code) → Prop)
    (pointSum : (Fin 9 → Code) → Target) (target : Target)
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

#print axioms GateReplacement.exact_gate_substitution

end GateReplacement
