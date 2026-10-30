module

public import Mathlib.Algebra.Group.Basic

/-!
The pair index stores signed singleton and distinct-pair sums. These identities
are the group-theoretic bridge from a zero-sum support of size at most four to
a complement lookup. The executable index-order partition is audited against
the exhaustive enumerator on sealed traces.
-/

namespace PairIndexCancellation

variable {G : Type*} [AddCommGroup G]

public theorem two_cancel_iff (a b : G) : a + b = 0 ↔ b = -a := by
  rw [eq_neg_iff_add_eq_zero, add_comm]

public theorem three_cancel_iff (a b c : G) :
    a + b + c = 0 ↔ c = -(a + b) := by
  rw [eq_neg_iff_add_eq_zero, add_comm]

public theorem four_cancel_iff (a b c d : G) :
    a + b + c + d = 0 ↔ c + d = -(a + b) := by
  rw [add_assoc (a + b) c d, eq_neg_iff_add_eq_zero, add_comm (c + d) (a + b)]

#print axioms two_cancel_iff
#print axioms three_cancel_iff
#print axioms four_cancel_iff

end PairIndexCancellation
