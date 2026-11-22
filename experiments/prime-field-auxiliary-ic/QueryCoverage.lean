import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace M31QueryCoverage
variable {G I : Type*} [DecidableEq G]

/-- Starts that hit a point in accepted on at least one query.
Each query is a permutation of the uniformly chosen start. -/
def hits (queries : Finset I) (schedule : I → Equiv.Perm G) (accepted : Finset G) :=
  queries.biUnion (fun i => accepted.map (schedule i).symm.toEmbedding)

theorem mem_hits (queries : Finset I) (schedule : I → Equiv.Perm G)
    (accepted : Finset G) (start : G) :
    start ∈ hits queries schedule accepted ↔ ∃ i ∈ queries, schedule i start ∈ accepted := by
  simp [hits]

theorem starts_bound (queries : Finset I) (schedule : I → Equiv.Perm G)
    (accepted : Finset G) :
    (hits queries schedule accepted).card ≤ queries.card * accepted.card := by
  apply Finset.card_biUnion_le_card_mul
  simp

/-- With the archived incidence count, any fixed schedule of this many
queries has strictly less than half the possible starts hitting. -/
theorem below_half (q : Nat) (small : q < 1857704) :
    2*q*578 < 2147505293 := by omega

#print axioms starts_bound
#print axioms mem_hits
end M31QueryCoverage
