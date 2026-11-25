/- Generic soundness of an affine XOR enclosure for a finite block. -/
namespace BlockSpanSoundness

def rejected (anchor : Nat) (directions allowed : Nat → Prop) : Prop :=
  ∀ d, directions d → ¬ allowed (anchor ^^^ d)

theorem rejected_family_has_no_allowed_member
    (anchor : Nat) (directions allowed family : Nat → Prop)
    (enclosure : ∀ x, family x → ∃ d, directions d ∧ x = anchor ^^^ d)
    (gate : rejected anchor directions allowed) :
    ∀ x, family x → ¬ allowed x := by
  intro x hx hxAllowed
  obtain ⟨d, hd, hxd⟩ := enclosure x hx
  exact gate d hd (hxd ▸ hxAllowed)

-- When every XOR displacement is allowed as a direction, the gate cannot
-- reject a block if zero is allowed: choose d = anchor.
theorem full_direction_space_prevents_rejection
    (anchor : Nat) (directions allowed : Nat → Prop)
    (full : ∀ d, directions d) (zero_allowed : allowed 0) :
    ¬ rejected anchor directions allowed := by
  intro gate
  have h := gate anchor (full anchor)
  simp only [Nat.xor_self] at h
  exact h zero_allowed

#print axioms rejected_family_has_no_allowed_member
#print axioms full_direction_space_prevents_rejection
end BlockSpanSoundness
