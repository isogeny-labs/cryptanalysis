/-!
A simple local root supplies a fixed root for Frobenius. This module proves
the regular V4 action implication; the Hensel and exact-field bridges are
recorded separately in the result note.
-/
namespace J1728SimpleRootShortcut

abbrev RootLabel := Bool × Bool

def act (g x : RootLabel) : RootLabel :=
  (xor g.1 x.1, xor g.2 x.2)

theorem nonidentity_has_no_fixed_root (g : RootLabel)
    (h : g ≠ (false, false)) (x : RootLabel) : act g x ≠ x := by
  cases g with
  | mk a b =>
    cases a <;> cases b <;> cases x with
    | mk c d => cases c <;> cases d <;> simp_all [act]

theorem one_fixed_root_forces_identity (g x : RootLabel)
    (h : act g x = x) : g = (false, false) := by
  by_cases hg : g = (false, false)
  · exact hg
  · exact False.elim (nonidentity_has_no_fixed_root g hg x h)

theorem one_fixed_root_forces_all_four_fixed (g x : RootLabel)
    (h : act g x = x) : ∀ y : RootLabel, act g y = y := by
  have hg := one_fixed_root_forces_identity g x h
  subst g
  intro y
  cases y with
  | mk a b => cases a <;> cases b <;> decide

/-- A two-cycle rules out the identity, so the regular V4 action has two
    two-cycles and no fixed roots. -/
theorem one_two_cycle_forces_all_orbits_two (g x : RootLabel)
    (h : act g x ≠ x) :
    ∀ y : RootLabel, act g y ≠ y ∧ act g (act g y) = y := by
  intro y
  cases g with
  | mk a b =>
    cases a <;> cases b <;> cases x with
    | mk c d =>
      cases c <;> cases d <;> cases y with
      | mk e f => cases e <;> cases f <;> simp_all [act]

#print axioms nonidentity_has_no_fixed_root
#print axioms one_fixed_root_forces_identity
#print axioms one_fixed_root_forces_all_four_fixed
#print axioms one_two_cycle_forces_all_orbits_two

end J1728SimpleRootShortcut
