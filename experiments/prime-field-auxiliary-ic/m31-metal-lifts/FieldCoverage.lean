import Lean

namespace M31Census

/-- Each canonical coordinate appears at a unique batch, worker, and iteration.
The final bound excludes the unused all-ones word in the last batch. -/
private def represents (x : Nat) (t : Nat × Nat × Nat) : Prop :=
      t.1 < 32 ∧ t.2.1 < 65536 ∧ t.2.2 < 1024 ∧
      t.2.1 + 65536*t.2.2 < min (2^26) (2147483647 - 2^26*t.1) ∧
      x = 2^26*t.1 + t.2.1 + 65536*t.2.2

theorem coverage (x : Nat) (hx : x < 2147483647) :
    ∃ t, represents x t ∧ ∀ u, represents x u → u = t := by
  refine ⟨(x / 67108864, x % 65536, (x % 67108864) / 65536), ?_, ?_⟩
  · dsimp [represents]
    omega
  · intro u h
    obtain ⟨b,w,i⟩ := u
    dsimp [represents] at h ⊢
    apply Prod.ext
    · dsimp; omega
    · apply Prod.ext <;> dsimp <;> omega

end M31Census
