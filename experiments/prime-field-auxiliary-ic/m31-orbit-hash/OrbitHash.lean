import Lean

/-! The even-first signed pair rows cover every full pair sum up to negation.
    This is a combinatorial/group-law fact, not a proof of machine-code timing. -/

namespace OrbitHash

def flip (k : Nat) : Nat := if k % 2 = 0 then k + 1 else k - 1

theorem flip_bounds (m k : Nat) (hk : k < 2 * m) : flip k < 2 * m := by
  unfold flip
  by_cases h : k % 2 = 0
  · simp [h]
    omega
  · simp [h]
    omega

theorem flip_even_of_odd (k : Nat) (hk : k % 2 = 1) : flip k % 2 = 0 := by
  unfold flip
  simp [show k % 2 ≠ 0 by omega]
  omega

theorem flip_order_of_odd (i j : Nat) (hi : i % 2 = 1) (hij : i ≤ j) :
    flip i ≤ flip j := by
  unfold flip
  have hne : i % 2 ≠ 0 := by omega
  simp [hne]
  by_cases hj : j % 2 = 0
  · simp [hj]
    omega
  · simp [hj]
    omega

theorem even_first_coverage {G : Type} [Add G] [Neg G]
    (signed : Nat → G) (m i j : Nat)
    (hi : i < 2 * m) (hj : j < 2 * m) (hij : i ≤ j)
    (hflip : ∀ k < 2 * m, signed (flip k) = -signed k)
    (hneg_add : ∀ a b : G, -(a + b) = -a + -b) :
    ∃ u v, u < 2 * m ∧ v < 2 * m ∧ u ≤ v ∧ u % 2 = 0 ∧
      (signed u + signed v = signed i + signed j ∨
       signed u + signed v = -(signed i + signed j)) := by
  by_cases he : i % 2 = 0
  · exact ⟨i, j, hi, hj, hij, he, Or.inl rfl⟩
  · have ho : i % 2 = 1 := by omega
    refine ⟨flip i, flip j, flip_bounds m i hi, flip_bounds m j hj,
      flip_order_of_odd i j ho hij, flip_even_of_odd i ho, Or.inr ?_⟩
    rw [hflip i hi, hflip j hj]
    exact (hneg_add (signed i) (signed j)).symm

end OrbitHash

#print axioms OrbitHash.even_first_coverage
