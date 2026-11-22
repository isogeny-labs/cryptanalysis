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

private theorem xor_swap (x y z : Nat) :
    Nat.xor x (Nat.xor y z) = Nat.xor y (Nat.xor x z) := by
  calc
    Nat.xor x (Nat.xor y z) = Nat.xor (Nat.xor x y) z :=
      (Nat.xor_assoc x y z).symm
    _ = Nat.xor (Nat.xor y x) z :=
      congrArg (fun v => Nat.xor v z) (Nat.xor_comm x y)
    _ = Nat.xor y (Nat.xor x z) := Nat.xor_assoc y x z

private theorem xor_cancel_prefix (a z : Nat) :
    Nat.xor a (Nat.xor a z) = z := by
  calc
    Nat.xor a (Nat.xor a z) = Nat.xor (Nat.xor a a) z :=
      (Nat.xor_assoc a a z).symm
    _ = z := by simp

private theorem outer_pair_cancel (a x rest : Nat) :
    Nat.xor a (Nat.xor (Nat.xor a x) rest) = Nat.xor x rest := by
  calc
    Nat.xor a (Nat.xor (Nat.xor a x) rest) =
        Nat.xor (Nat.xor a (Nat.xor a x)) rest :=
      (Nat.xor_assoc a (Nat.xor a x) rest).symm
    _ = Nat.xor x rest := by rw [xor_cancel_prefix]

private theorem inner_pair_cancel (a x y rest : Nat) :
    Nat.xor (Nat.xor a x) (Nat.xor (Nat.xor a y) rest) =
      Nat.xor x (Nat.xor y rest) := by
  calc
    Nat.xor (Nat.xor a x) (Nat.xor (Nat.xor a y) rest) =
        Nat.xor a (Nat.xor x (Nat.xor (Nat.xor a y) rest)) :=
      Nat.xor_assoc a x _
    _ = Nat.xor a (Nat.xor x (Nat.xor a (Nat.xor y rest))) :=
      congrArg (fun w => Nat.xor a (Nat.xor x w)) (Nat.xor_assoc a y rest)
    _ = Nat.xor a (Nat.xor a (Nat.xor x (Nat.xor y rest))) := by
      exact congrArg (Nat.xor a) (xor_swap x a (Nat.xor y rest))
    _ = Nat.xor x (Nat.xor y rest) := xor_cancel_prefix a _

private theorem final_pair_cancel (a x y : Nat) :
    Nat.xor (Nat.xor a x) (Nat.xor a y) = Nat.xor x y := by
  simpa using inner_pair_cancel a x y 0

theorem cubicCoeff_of_differences (a d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat) :
    cubicCoeff a (Nat.xor a d₀) (Nat.xor a d₁) (Nat.xor a d₂)
      (Nat.xor a d₃) (Nat.xor a d₄) (Nat.xor a d₅) (Nat.xor a d₆) =
    xor7 d₀ d₁ d₂ d₃ d₄ d₅ d₆ := by
  unfold cubicCoeff xor7
  rw [outer_pair_cancel]
  rw [inner_pair_cancel]
  rw [inner_pair_cancel]
  rw [final_pair_cancel]

theorem nonzero_cubic_of_independent_differences
    (a d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat)
    (h : xor7 d₀ d₁ d₂ d₃ d₄ d₅ d₆ ≠ 0) :
    cubicCoeff a (Nat.xor a d₀) (Nat.xor a d₁) (Nat.xor a d₂)
      (Nat.xor a d₃) (Nat.xor a d₄) (Nat.xor a d₅) (Nat.xor a d₆) ≠ 0 := by
  rw [cubicCoeff_of_differences]
  exact h

def sevenIndependent (d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat) : Prop :=
  ∀ b₀ b₁ b₂ b₃ b₄ b₅ b₆ : Bool,
    b₀ = true ∨ b₁ = true ∨ b₂ = true ∨ b₃ = true ∨
    b₄ = true ∨ b₅ = true ∨ b₆ = true →
    xor7 (if b₀ then d₀ else 0) (if b₁ then d₁ else 0)
      (if b₂ then d₂ else 0) (if b₃ then d₃ else 0)
      (if b₄ then d₄ else 0) (if b₅ then d₅ else 0)
      (if b₆ then d₆ else 0) ≠ 0

theorem cubic_of_sevenIndependent (a d₀ d₁ d₂ d₃ d₄ d₅ d₆ : Nat)
    (h : sevenIndependent d₀ d₁ d₂ d₃ d₄ d₅ d₆) :
    cubicCoeff a (Nat.xor a d₀) (Nat.xor a d₁) (Nat.xor a d₂)
      (Nat.xor a d₃) (Nat.xor a d₄) (Nat.xor a d₅) (Nat.xor a d₆) ≠ 0 := by
  have hAll : xor7 d₀ d₁ d₂ d₃ d₄ d₅ d₆ ≠ 0 := by
    have hs := h true true true true true true true (by simp)
    simpa using hs
  exact nonzero_cubic_of_independent_differences a d₀ d₁ d₂ d₃ d₄ d₅ d₆ hAll

#print axioms CubicParity.cubicCoeff_of_differences
#print axioms CubicParity.nonzero_cubic_of_independent_differences
#print axioms CubicParity.cubic_of_sevenIndependent
end CubicParity
