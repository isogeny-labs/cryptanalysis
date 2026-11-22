import Std

/-! For a three-bit vector-valued function, the coefficient of the cubic ANF
monomial is the XOR of its eight values. Eight affinely independent values
have nonzero cubic coefficient under every labeling of the eight inputs. -/
namespace CubicParity

def xor7 (d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat) : Nat :=
  Nat.xor d₀ (Nat.xor d₁ (Nat.xor d₂ (Nat.xor d₃
    (Nat.xor d₄ (Nat.xor d₅ d₆)))))

def cubicCoeff (v₀ v₁ v₂ v₃ v₄ v₅ v₆ v₇ : Nat) : Nat :=
  Nat.xor v₀ (Nat.xor v₁ (Nat.xor v₂ (Nat.xor v₃
    (Nat.xor v₄ (Nat.xor v₅ (Nat.xor v₆ v₇))))))

private theorem xor_left_comm (x y z : Nat) :
    Nat.xor x (Nat.xor y z) = Nat.xor y (Nat.xor x z) := by
  rw [← Nat.xor_assoc, Nat.xor_comm x y, Nat.xor_assoc]

theorem cubicCoeff_of_differences (a d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat) :
    cubicCoeff a (Nat.xor a d₀) (Nat.xor a d₁) (Nat.xor a d₂)
      (Nat.xor a d₃) (Nat.xor a d₄) (Nat.xor a d₅) (Nat.xor a d₆) =
    xor7 d₀ d₁ d₂ d₃ d₄ d₅ d₆ := by
  simp [cubicCoeff, xor7, Nat.xor_assoc, xor_left_comm]

theorem nonzero_cubic_of_independent_differences
    (a d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat)
    (h : xor7 d₀ d₁ d₂ d₃ d₄ d₅ d₆ ≠ 0) :
    cubicCoeff a (Nat.xor a d₀) (Nat.xor a d₁) (Nat.xor a d₂)
      (Nat.xor a d₃) (Nat.xor a d₄) (Nat.xor a d₅) (Nat.xor a d₆) ≠ 0 := by
  rw [cubicCoeff_of_differences]
  exact h

#print axioms CubicParity.cubicCoeff_of_differences
#print axioms CubicParity.nonzero_cubic_of_independent_differences
end CubicParity
