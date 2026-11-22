import Std

namespace QuotientFingerprint

def indicator : List (Bool × Bool) → Bool
  | [] => true
  | (bit, target) :: rest => (bit == target) && indicator rest

theorem indicator_true_iff_all_equal (pairs : List (Bool × Bool)) :
    indicator pairs = true ↔ ∀ pair ∈ pairs, pair.1 = pair.2 := by
  induction pairs with
  | nil => simp [indicator]
  | cons pair rest ih =>
      cases pair with
      | mk bit target =>
          cases bit <;> cases target <;> simp [indicator, ih]

theorem indicator_zero_excludes_exact (pairs : List (Bool × Bool))
    (hzero : indicator pairs = false) :
    ¬ (∀ pair ∈ pairs, pair.1 = pair.2) := by
  intro hall
  have htrue := (indicator_true_iff_all_equal pairs).2 hall
  simp [hzero] at htrue

theorem indicator_append (front suffix : List (Bool × Bool)) :
    indicator (front ++ suffix) = (indicator front && indicator suffix) := by
  induction front with
  | nil => simp [indicator]
  | cons pair rest ih =>
      cases pair with
      | mk bit target =>
          simp [indicator, ih, Bool.and_assoc]

theorem zero_persists (front suffix : List (Bool × Bool))
    (hzero : indicator front = false) :
    indicator (front ++ suffix) = false := by
  rw [indicator_append, hzero]
  rfl

#print axioms indicator_true_iff_all_equal
#print axioms indicator_zero_excludes_exact
#print axioms zero_persists

end QuotientFingerprint
