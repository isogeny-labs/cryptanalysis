import Std

/-! Trace obstruction for the first-order S3 bilinear span, and the pivot
identity used to restore rank-one products. Field-specific trace laws and
the full finite-field dimension statement are recorded in PROOF_MAP.md. -/
namespace BilinearGate

variable {F : Type} [Mul F]

theorem artin_schreier_trace_zero
    [Add F]
    (tr : F → Bool)
    (hadd : ∀ x y : F, tr (x + y) = (tr x).xor (tr y))
    (hsquare : ∀ x : F, tr (x * x) = tr x)
    (z : F) : tr (z * z + z) = false := by
  rw [hadd, hsquare]
  cases tr z <;> rfl

theorem bilinear_column_trace_zero
    [Add F]
    (tr : F → Bool)
    (hadd : ∀ x y : F, tr (x + y) = (tr x).xor (tr y))
    (hsquare : ∀ x : F, tr (x * x) = tr x)
    (t c d : F) :
    tr ((t * (c * d)) * (t * (c * d)) + t * (c * d)) = false := by
  exact artin_schreier_trace_zero tr hadd hsquare (t * (c * d))

theorem square_column_trace_zero
    (tr : F → Bool)
    (hsquare : ∀ x : F, tr (x * x) = tr x)
    (c : F) (hc : tr c = false) : tr (c * c) = false := by
  rw [hsquare, hc]

theorem pivot_row_is_right_vector
    {r s : Nat} (alpha : Fin r → Bool) (beta : Fin s → Bool)
    (gamma : Fin r → Fin s → Bool) (pivot : Fin r)
    (hpivot : alpha pivot = true)
    (hrankOne : ∀ i j, gamma i j = (alpha i).and (beta j)) :
    ∀ j, gamma pivot j = beta j := by
  intro j
  rw [hrankOne, hpivot]
  cases beta j <;> rfl

#print axioms BilinearGate.artin_schreier_trace_zero
#print axioms BilinearGate.bilinear_column_trace_zero
#print axioms BilinearGate.square_column_trace_zero
#print axioms BilinearGate.pivot_row_is_right_vector
end BilinearGate
