import Mathlib

namespace M31HashCollision

/-- Keep the two colliding parities separately, followed by every other label. -/
abbrev Boundary (B : Type*) := ZMod 2 × ZMod 2 × B

variable {E B : Type*} [AddCommGroup E] [AddCommGroup B]

def defect : Boundary B := (1, 1, 0)

def merge (v : Boundary B) : ZMod 2 × B := (v.1 + v.2.1, v.2.2)

private theorem parity (a b : ZMod 2) :
    a + b = 0 ↔ (a = 0 ∧ b = 0) ∨ (a = 1 ∧ b = 1) := by
  exact (by decide : ∀ i j : Fin 2, i + j = 0 ↔
    (i = 0 ∧ j = 0) ∨ (i = 1 ∧ j = 1)) a b

theorem merge_zero_iff (v : Boundary B) :
    merge v = 0 ↔ v = 0 ∨ v = defect := by
  obtain ⟨a, b, r⟩ := v
  simp only [merge, defect, Prod.ext_iff]
  change (a + b = 0 ∧ r = 0) ↔
    (a = 0 ∧ b = 0 ∧ r = 0) ∨ (a = 1 ∧ b = 1 ∧ r = 0)
  rw [parity]
  tauto

variable (boundary : E →+ Boundary B)

def fiber (v : Boundary B) : Set E := {x | boundary x = v}

def accepted : Set E := {x | merge (boundary x) = 0}

theorem partition : accepted boundary = fiber boundary 0 ∪ fiber boundary defect := by
  ext x
  exact merge_zero_iff _

/-- Translation by one witness pairs every genuinely closed selection with a
unique selection whose endpoints are precisely the two colliding labels. -/
def translate (w : E) (hw : boundary w = defect) :
    fiber boundary 0 ≃ fiber boundary defect where
  toFun x := ⟨x.val + w, by
    change boundary (x.val + w) = defect
    rw [map_add, show boundary x.val = 0 from x.property, zero_add, hw]⟩
  invFun y := ⟨y.val - w, by
    change boundary (y.val - w) = 0
    rw [map_sub, show boundary y.val = defect from y.property, hw]
    exact sub_self _⟩
  left_inv x := Subtype.ext (add_sub_cancel_right ..)
  right_inv y := Subtype.ext (sub_add_cancel ..)

open Classical in
theorem acceptedCount [Finite E] :
    (accepted boundary).ncard =
      if defect ∈ Set.range boundary then 2 * (fiber boundary 0).ncard
      else (fiber boundary 0).ncard := by
  classical
  rw [partition, Set.ncard_union_eq]
  · split
    · rename_i h
      obtain ⟨w, hw⟩ := h
      rw [← Set.ncard_congr' (translate boundary w hw)]
      omega
    · rename_i h
      have hempty : fiber boundary defect = ∅ := Set.eq_empty_iff_forall_notMem.mpr
        (fun x hx => h ⟨x, hx⟩)
      simp [hempty]
  · apply Set.disjoint_left.mpr
    intro x hx hy
    have eq := (show boundary x = 0 from hx).symm.trans (show boundary x = defect from hy)
    have bad := congrArg Prod.fst eq
    exact zero_ne_one (α := ZMod 2) bad

end M31HashCollision
