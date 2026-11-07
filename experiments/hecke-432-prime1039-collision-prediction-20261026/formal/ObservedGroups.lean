import Std

namespace P1231ObservedGroups

def groups : List (Nat × Nat × Nat) := [
    (1, 0, 24),
    (19, 48, 0),
    (49, 48, 0),
    (112, 48, 0),
    (126, 0, 24),
    (208, 48, 0),
    (233, 48, 0),
    (357, 48, 0),
    (380, 48, 0),
    (466, 48, 0),
    (548, 48, 0),
    (571, 48, 0),
    (641, 48, 0),
    (666, 48, 0),
    (690, 48, 0),
    (691, 48, 0),
    (751, 48, 0),
    (770, 48, 0),
    (859, 48, 0),
    (875, 48, 0),
    (896, 48, 0),
    (980, 48, 0),
    (1002, 48, 0),
    (1045, 48, 0),
    (1070, 48, 0),
    (1102, 48, 0),
    (1104, 0, 24),
    (1137, 48, 0),
    (1163, 48, 0),
    (1184, 48, 0)]

/-- The 30 observed x-coordinate classes have double fibers exactly
at the three cube roots of one. The audit binds these compressed counts
to all 1,368 concrete (C,E,B) rows and the independent source census. -/
theorem double_iff_special :
    groups.all (fun g => decide (g.2.2 > 0 ↔ g.1^3 % 1231 = 1)) = true := by decide

theorem single_double_totals :
    groups.foldl (fun a g => (a.1 + g.2.1, a.2 + g.2.2)) (0, 0) =
      (1296, 72) := by decide

theorem group_count : groups.length = 30 := by decide

#print axioms double_iff_special
#print axioms single_double_totals
#print axioms group_count

end P1231ObservedGroups
