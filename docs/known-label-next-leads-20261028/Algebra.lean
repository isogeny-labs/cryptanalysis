import Mathlib

/- Proposed source only: no Lean runtime was available for this note.
These ring identities are the feasible algebraic core, not formal proofs of
the graph-to-elliptic-group bridge or the probability theorem in README.md. -/
namespace KnownLabelLeads

variable {K : Type*} [CommRing K]

theorem triangle_identity (a b c : K) :
    2 * a = (a + b) - (b + c) + (c + a) := by ring

theorem signed_second_moment (a b c : K) :
    (a + b - c)^2 - (a^2 + b^2 - c^2) = 2 * (a-c) * (b-c) := by ring

theorem signed_third_moment (a b c : K) :
    -(a+b-c)^3 + 3*(a+b-c)*(a^2+b^2-c^2) - 2*(a^3+b^3-c^3) =
      6*c*(a-c)*(b-c) := by ring

theorem positive_pair_product (a b c : K) :
    2*a*b = (a+b-c)^2 - (a^2+b^2-c^2) + 2*c*(a+b-c) := by ring

#print axioms triangle_identity
#print axioms signed_second_moment
#print axioms signed_third_moment
#print axioms positive_pair_product

end KnownLabelLeads
