import FiberLift

namespace M31ResidueBitmap
abbrev F := ZMod 2147483647
abbrev half := 1073741823

-- Every square has a root in the enumerated lower half, including zero.
theorem half_root (a : F) :
    (∃ y : F, y.val ≤ half ∧ y^2 = a) ↔ ∃ y : F, y^2 = a := by
  constructor
  · rintro ⟨y,_,eq⟩
    exact ⟨y,eq⟩
  · rintro ⟨y,eq⟩
    by_cases small : y.val ≤ half
    · exact ⟨y,small,eq⟩
    · have nz : y ≠ 0 := by rintro rfl; simp at small
      let _ : NeZero y := ⟨nz⟩
      refine ⟨-y,?_,by simpa using eq⟩
      rw [ZMod.val_neg_of_ne_zero]
      unfold half at *
      omega

theorem complement (a : F) (nz : a ≠ 0) :
    (¬ ∃ y : F, y^2 = -a) ↔ ∃ y : F, y^2 = a := by
  have base := M31FiberLift.lift_exact (fun _ : Unit => a) ()
  rw [M31FiberLift.lane_power] at base
  have split := M31FiberLift.twist_split a
  rw [← M31FiberLift.twist_lift_exact, ← base]
  exact ⟨fun h => split.1.resolve_right h, fun h h' => nz (split.2.mp ⟨h,h'⟩)⟩

def stored (a : F) := ∃ y : F, y.val ≤ half ∧ y^2 = a

theorem lookup (a : F) :
    (if a.val ≤ half then stored a else ¬ stored (-a)) ↔ ∃ y : F, y^2 = a := by
  split
  · exact half_root a
  · rename_i high
    have nz : a ≠ 0 := by rintro rfl; simp at high
    exact (not_congr (half_root (-a))).trans (complement a nz)

end M31ResidueBitmap
