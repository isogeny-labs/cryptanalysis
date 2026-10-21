/-!
# Pair-index correctness for the orbit-quotient toy experiment

`orbit_core.py` stores residues of two selected orbit representatives, then
looks up the complement of a third representative. This theorem proves that
such a lookup is equivalent to the direct three-summand compatibility test.
The lists model the *already enumerated* scalar representatives of one key
per slot. It does not certify their enumeration, the curve arithmetic, the
measured densities, Boolean degrees, or any ECDLP speedup.
-/
namespace OrbitQuotient

/-- Residue keys stored by the two-slot meet-in-the-middle index. -/
def pairTotals (r : Nat) (A B : List Nat) : List Nat :=
  A.flatMap fun a => B.map fun b => (a + b) % r

/-- Membership in the index is exactly membership in the enumerated pair sums. -/
theorem mem_pairTotals_iff (r s : Nat) (A B : List Nat) :
    s ∈ pairTotals r A B ↔ ∃ a ∈ A, ∃ b ∈ B, (a + b) % r = s := by
  simp [pairTotals, List.mem_flatMap, List.mem_map]

/-- A three-slot compatibility query is equivalent to a pair-index lookup. -/
theorem triple_matches_iff_pair_lookup (r t : Nat) (A B C : List Nat) :
    (∃ a ∈ A, ∃ b ∈ B, ∃ c ∈ C, (a + b + c) % r = t % r) ↔
    (∃ s ∈ pairTotals r A B, ∃ c ∈ C, (s + c) % r = t % r) := by
  constructor
  · rintro ⟨a, ha, b, hb, c, hc, h⟩
    refine ⟨(a + b) % r, ?_, c, hc, ?_⟩
    · exact (mem_pairTotals_iff r ((a + b) % r) A B).2 ⟨a, ha, b, hb, rfl⟩
    · rw [Nat.mod_add_mod]
      exact h
  · rintro ⟨s, hs, c, hc, h⟩
    obtain ⟨a, ha, b, hb, hab⟩ := (mem_pairTotals_iff r s A B).1 hs
    refine ⟨a, ha, b, hb, c, hc, ?_⟩
    rw [← hab] at h
    rw [Nat.mod_add_mod] at h
    exact h

end OrbitQuotient
