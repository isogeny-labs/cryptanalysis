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


section ArbitraryBuckets

variable {V W : Type*} [AddCommGroup V] [AddCommGroup W]

/-- Every attainable boundary erased by the bucket map has exactly as many
preimages as the genuine zero boundary. -/
private noncomputable def splitAccepted (d : E →+ V) (h : V →+ W) :
    {x : E // h (d x) = 0} ≃
    {v : V // v ∈ Set.range d ∧ h v = 0} × {x : E // d x = 0} := by
  classical
  let pick (v : {v : V // v ∈ Set.range d ∧ h v = 0}) := v.property.1.choose
  have picked (v) : d (pick v) = v.val := v.property.1.choose_spec
  let label (x : {x : E // h (d x) = 0}) :
      {v : V // v ∈ Set.range d ∧ h v = 0} := ⟨d x, ⟨x, rfl⟩, x.property⟩
  refine {
    toFun := fun x => (label x, ⟨x.val - pick (label x), ?_⟩)
    invFun := fun y => ⟨y.2.val + pick y.1, ?_⟩
    left_inv := ?_
    right_inv := ?_ }
  · rw [map_sub, picked]
    exact sub_self _
  · rw [map_add, y.2.property, zero_add, picked]
    exact y.1.property.2
  · intro x
    exact Subtype.ext (sub_add_cancel ..)
  · rintro ⟨v, x⟩
    have hl : label ⟨x.val + pick v, by simp [picked, x.property, v.property.2]⟩ = v := by
      apply Subtype.ext
      change d (x.val + pick v) = v.val
      simp [picked, x.property]
    apply Prod.ext
    · exact hl
    · apply Subtype.ext
      change x.val + pick v - pick (label _) = x.val
      rw [hl, add_sub_cancel_right]

theorem bucketCount [Finite E] (d : E →+ V) (h : V →+ W) :
    Nat.card {x : E // h (d x) = 0} =
      Nat.card {v : V // v ∈ Set.range d ∧ h v = 0} *
      Nat.card {x : E // d x = 0} := by
  rw [Nat.card_congr (splitAccepted d h), Nat.card_prod]

end ArbitraryBuckets

end M31HashCollision
