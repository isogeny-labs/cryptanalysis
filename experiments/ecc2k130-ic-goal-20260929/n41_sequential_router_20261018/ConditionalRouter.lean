import Std

namespace ConditionalRouter

def passes {X : Type} (gates : List (X → Bool)) (x : X) : Prop :=
  ∀ gate, gate ∈ gates → gate x = false

/-- Replacing the next gate by an exact formula on the family domain
surviving earlier gates preserves the accepted set on that domain. -/
theorem conditional_replacement {X : Type}
    (domain : X → Prop) (earlier : List (X → Bool))
    (oldGate newGate : X → Bool)
    (hagrees : ∀ x, domain x → passes earlier x →
      oldGate x = newGate x) (x : X) (hx : domain x) :
    passes (earlier ++ [oldGate]) x ↔
    passes (earlier ++ [newGate]) x := by
  constructor
  · intro h gate hmem
    simp only [passes, List.mem_append, List.mem_singleton] at h hmem
    rcases hmem with hearlier | hnew
    · exact h gate (Or.inl hearlier)
    · subst gate
      have hp : passes earlier x := by
        intro f hf
        exact h f (Or.inl hf)
      rw [← hagrees x hx hp]
      exact h oldGate (Or.inr rfl)
  · intro h gate hmem
    simp only [passes, List.mem_append, List.mem_singleton] at h hmem
    rcases hmem with hearlier | hold
    · exact h gate (Or.inl hearlier)
    · subst gate
      have hp : passes earlier x := by
        intro f hf
        exact h f (Or.inl hf)
      rw [hagrees x hx hp]
      exact h newGate (Or.inr rfl)

#print axioms conditional_replacement

end ConditionalRouter
