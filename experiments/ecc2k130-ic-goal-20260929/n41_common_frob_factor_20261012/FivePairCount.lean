import Std

/-! The multiplicative lower bound follows from one extension bound at each
    depth. The source-specific incidence and support census are executable
    certificates, not yet imported into this Lean module. -/

theorem five_pair_count_from_extension_bounds
    (states incidence c1 c2 c3 c4 c5 : Nat)
    (h1 : states ≤ c1)
    (h2 : c1 * (states - 2 * incidence) ≤ c2)
    (h3 : c2 * (states - 4 * incidence) ≤ c3)
    (h4 : c3 * (states - 6 * incidence) ≤ c4)
    (h5 : c4 * (states - 8 * incidence) ≤ c5) :
    (((states * (states - 2 * incidence)) *
      (states - 4 * incidence)) *
      (states - 6 * incidence)) *
      (states - 8 * incidence) ≤ c5 := by
  have t2 : states * (states - 2 * incidence) ≤ c2 :=
    Nat.le_trans (Nat.mul_le_mul_right _ h1) h2
  have t3 : (states * (states - 2 * incidence)) *
      (states - 4 * incidence) ≤ c3 :=
    Nat.le_trans (Nat.mul_le_mul_right _ t2) h3
  have t4 : ((states * (states - 2 * incidence)) *
      (states - 4 * incidence)) * (states - 6 * incidence) ≤ c4 :=
    Nat.le_trans (Nat.mul_le_mul_right _ t3) h4
  exact Nat.le_trans (Nat.mul_le_mul_right _ t4) h5

#print axioms five_pair_count_from_extension_bounds
