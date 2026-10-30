import Mathlib.Algebra.Ring.Defs
import Mathlib.Tactic.Ring

namespace J1728QuarticResolvent

variable {R : Type*} [CommRing R] (r₁ r₂ r₃ r₄ : R)

private def qa : R := -(r₁ + r₂ + r₃ + r₄)
private def qb : R :=
  r₁ * r₂ + r₁ * r₃ + r₁ * r₄ + r₂ * r₃ + r₂ * r₄ + r₃ * r₄
private def qc : R :=
  -(r₁ * r₂ * r₃ + r₁ * r₂ * r₄ + r₁ * r₃ * r₄ + r₂ * r₃ * r₄)
private def qd : R := r₁ * r₂ * r₃ * r₄

private def cubic (a b c d y : R) : R :=
  y ^ 3 - b * y ^ 2 + (a * c - 4 * d) * y + (4 * b * d - a ^ 2 * d - c ^ 2)

theorem pair_12_34_is_resolvent_root :
    cubic (qa r₁ r₂ r₃ r₄) (qb r₁ r₂ r₃ r₄)
      (qc r₁ r₂ r₃ r₄) (qd r₁ r₂ r₃ r₄) (r₁ * r₂ + r₃ * r₄) = 0 := by
  unfold cubic qa qb qc qd
  ring

theorem pair_13_24_is_resolvent_root :
    cubic (qa r₁ r₂ r₃ r₄) (qb r₁ r₂ r₃ r₄)
      (qc r₁ r₂ r₃ r₄) (qd r₁ r₂ r₃ r₄) (r₁ * r₃ + r₂ * r₄) = 0 := by
  unfold cubic qa qb qc qd
  ring

theorem pair_14_23_is_resolvent_root :
    cubic (qa r₁ r₂ r₃ r₄) (qb r₁ r₂ r₃ r₄)
      (qc r₁ r₂ r₃ r₄) (qd r₁ r₂ r₃ r₄) (r₁ * r₄ + r₂ * r₃) = 0 := by
  unfold cubic qa qb qc qd
  ring

theorem pair_sum_difference_square :
    ((r₁ + r₂) - (r₃ + r₄)) ^ 2 =
      (qa r₁ r₂ r₃ r₄) ^ 2 - 4 * (qb r₁ r₂ r₃ r₄) +
        4 * (r₁ * r₂ + r₃ * r₄) := by
  unfold qa qb
  ring

#print axioms pair_12_34_is_resolvent_root
#print axioms pair_13_24_is_resolvent_root
#print axioms pair_14_23_is_resolvent_root
#print axioms pair_sum_difference_square

end J1728QuarticResolvent
