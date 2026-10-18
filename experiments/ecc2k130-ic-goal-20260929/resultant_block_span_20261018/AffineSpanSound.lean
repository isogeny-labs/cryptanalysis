import Std

namespace AffineSpanSound

def xorSpan (generators : List Nat) (value : Nat) : Prop :=
  ∃ chosen : List Nat,
    (∀ x, x ∈ chosen → x ∈ generators) ∧
    chosen.foldl Nat.xor 0 = value

def rejects (base : Nat) (rest : List Nat) : Prop :=
  ¬ xorSpan (rest.map (fun value => Nat.xor value base)) base

/-- If the affine-span test rejects, neither the block base output nor any
other enumerated block output is zero. The rank basis in the implementation
is a representation of this XOR span. -/
theorem rejected_block_has_no_zero (base : Nat) (rest : List Nat)
    (h : rejects base rest) : base ≠ 0 ∧ 0 ∉ rest := by
  constructor
  · intro hb
    subst base
    apply h
    refine ⟨[], ?_, ?_⟩
    · intro x hx
      simp at hx
    · rfl
  · intro hz
    apply h
    refine ⟨[base], ?_, ?_⟩
    · intro x hx
      have heq : x = base := by simpa using hx
      subst x
      apply List.mem_map.mpr
      exact ⟨0, hz, by simp⟩
    · simp

#print axioms rejected_block_has_no_zero

end AffineSpanSound
