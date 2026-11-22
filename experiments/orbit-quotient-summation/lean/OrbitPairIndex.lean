/-!
# Pair-index correctness for the orbit-quotient toy experiment

`orbit_core.py` stores residues of two selected orbit representatives, then
looks up the complement of a third representative or a second pair. These
theorems prove that the lookups are equivalent to the direct three- and
four-summand compatibility tests.
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

/-- The four-slot support tested by `m4_stats` is exactly the support of a
left pair total and a complementary right pair total. This concerns
existence of a tuple, not the number of witnesses stored in each bucket. -/
theorem quadruple_matches_iff_two_pair_lookup (r t : Nat)
    (A B C D : List Nat) :
    (∃ a ∈ A, ∃ b ∈ B, ∃ c ∈ C, ∃ d ∈ D,
      (a + b + c + d) % r = t % r) ↔
    (∃ s ∈ pairTotals r A B, ∃ u ∈ pairTotals r C D,
      (s + u) % r = t % r) := by
  constructor
  · rintro ⟨a, ha, b, hb, c, hc, d, hd, h⟩
    refine ⟨(a + b) % r, ?_, (c + d) % r, ?_, ?_⟩
    · exact (mem_pairTotals_iff r ((a + b) % r) A B).2 ⟨a, ha, b, hb, rfl⟩
    · exact (mem_pairTotals_iff r ((c + d) % r) C D).2 ⟨c, hc, d, hd, rfl⟩
    · simpa only [Nat.mod_add_mod, Nat.add_mod_mod, Nat.add_assoc] using h
  · rintro ⟨s, hs, u, hu, h⟩
    obtain ⟨a, ha, b, hb, hab⟩ := (mem_pairTotals_iff r s A B).1 hs
    obtain ⟨c, hc, d, hd, hcd⟩ := (mem_pairTotals_iff r u C D).1 hu
    refine ⟨a, ha, b, hb, c, hc, d, hd, ?_⟩
    rw [← hab, ← hcd] at h
    simpa only [Nat.mod_add_mod, Nat.add_mod_mod, Nat.add_assoc] using h

end OrbitQuotient
