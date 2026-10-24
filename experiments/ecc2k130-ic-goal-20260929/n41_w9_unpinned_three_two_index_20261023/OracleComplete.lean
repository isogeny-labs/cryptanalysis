import Std
import Init.Grind.Ring.Basic
import Init.Grind.Ring.Field

open Lean.Grind

/-! Exactness of a coordinate-root index followed by a group-sum check.
The chart and root-enumerator bridge is an explicit hypothesis. -/
namespace OracleComplete

variable {Point Coord : Type}
variable (add : Point → Point → Point)
variable (coord : Point → Coord)
variable (eligible : Point → Point → Prop)
variable (left right : List Point)
variable (roots : Coord → Coord → List Coord)
variable (lookup : Coord → List Point)

def Witness (target : Point) : Prop :=
  ∃ a, a ∈ left ∧ ∃ b, b ∈ right ∧
    eligible a b ∧ add a b = target

def Hit (target : Point) : Prop :=
  ∃ a, a ∈ left ∧ ∃ x, x ∈ roots (coord a) (coord target) ∧
    ∃ b, b ∈ lookup x ∧ eligible a b ∧ add a b = target

theorem complete
    (target : Point)
    (root_complete : ∀ a b : Point,
      eligible a b → add a b = target →
      coord b ∈ roots (coord a) (coord target))
    (lookup_complete : ∀ b : Point,
      b ∈ right → b ∈ lookup (coord b)) :
    Witness add eligible left right target →
      Hit add coord eligible left roots lookup target := by
  rintro ⟨a, ha, b, hb, he, hs⟩
  exact ⟨a, ha, coord b, root_complete a b he hs,
    b, lookup_complete b hb, he, hs⟩

theorem sound
    (target : Point)
    (lookup_sound : ∀ x : Coord, ∀ b : Point,
      b ∈ lookup x → b ∈ right) :
    Hit add coord eligible left roots lookup target →
      Witness add eligible left right target := by
  rintro ⟨a, ha, x, _, b, hb, he, hs⟩
  exact ⟨a, ha, b, lookup_sound x b hb, he, hs⟩

theorem exact
    (target : Point)
    (root_complete : ∀ a b : Point,
      eligible a b → add a b = target →
      coord b ∈ roots (coord a) (coord target))
    (lookup_complete : ∀ b : Point,
      b ∈ right → b ∈ lookup (coord b))
    (lookup_sound : ∀ x : Coord, ∀ b : Point,
      b ∈ lookup x → b ∈ right) :
    Hit add coord eligible left roots lookup target ↔
      Witness add eligible left right target := by
  constructor
  · exact sound add coord eligible left right roots lookup target lookup_sound
  · exact complete add coord eligible left right roots lookup target
      root_complete lookup_complete

theorem quadratic_code_decode {F : Type} [Field F]
    (C p H b : F) (hchar : ∀ x : F, x+x = 0)
    (hC : C ≠ 0) (hb : b ≠ 0)
    (hpair : C*b*b+p*b+H = 0) :
    p/C = b+(H/C)/b := by
  have htwo : p*b = C*b*b+H := by
    have hsum : (C*b*b+H)+(p*b) = 0 := by
      calc
        (C*b*b+H)+(p*b) = C*b*b+p*b+H := by grind +ring
        _ = 0 := hpair
    have hneg : -(p*b) = p*b := by
      have hh := hchar (p*b)
      grind +ring
    grind +ring
  grind +ring

#print axioms complete
#print axioms sound
#print axioms exact
#print axioms quadratic_code_decode

end OracleComplete
