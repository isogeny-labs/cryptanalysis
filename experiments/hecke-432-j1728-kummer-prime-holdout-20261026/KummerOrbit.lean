/-!
The regular action of the rank-two sign group on four roots. The arithmetic
bridge is the identification of Frobenius with the two radicand characters.
-/
namespace J1728KummerHoldout

abbrev SignPair := Bool × Bool

def act (g x : SignPair) : SignPair := (xor g.1 x.1, xor g.2 x.2)

theorem identity_fixes_four (x : SignPair) : act (false, false) x = x := by
  cases x with
  | mk a b => cases a <;> cases b <;> decide

theorem nonidentity_is_fixed_point_free (g : SignPair)
    (h : g ≠ (false, false)) (x : SignPair) : act g x ≠ x := by
  cases g with
  | mk a b =>
    cases a <;> cases b <;> cases x with
    | mk c d => cases c <;> cases d <;> simp_all [act]

theorem every_orbit_has_length_at_most_two (g x : SignPair) :
    act g (act g x) = x := by
  cases g with
  | mk a b =>
    cases a <;> cases b <;> cases x with
    | mk c d => cases c <;> cases d <;> decide

theorem nonidentity_has_two_cycles (g : SignPair)
    (h : g ≠ (false, false)) (x : SignPair) :
    act g x ≠ x ∧ act g (act g x) = x := by
  exact ⟨nonidentity_is_fixed_point_free g h x,
    every_orbit_has_length_at_most_two g x⟩

#print axioms identity_fixes_four
#print axioms nonidentity_is_fixed_point_free
#print axioms every_orbit_has_length_at_most_two
#print axioms nonidentity_has_two_cycles

end J1728KummerHoldout
