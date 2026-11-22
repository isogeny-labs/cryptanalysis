import Std
import Init.Grind.Ring.Basic

namespace BackwardCut
open Lean.Grind

/-- The three backward partial sums are forced by an exact group endpoint
    and three fixed signed suffix points. -/
theorem necessary {G : Type} [AddCommGroup G] (s p12 p13 p14 endpoint : G)
    (h : ((s + p12) + p13) + p14 = endpoint) :
    s = ((endpoint - p14) - p13) - p12 := by
  have h12 : (s + p12) + p13 = endpoint - p14 := by
    calc
      (s + p12) + p13 = (((s + p12) + p13) + p14) - p14 :=
        AddCommGroup.add_sub_cancel.symm
      _ = endpoint - p14 := by rw [h]
  have h11 : s + p12 = (endpoint - p14) - p13 := by
    calc
      s + p12 = ((s + p12) + p13) - p13 :=
        AddCommGroup.add_sub_cancel.symm
      _ = (endpoint - p14) - p13 := by rw [h12]
  calc
    s = (s + p12) - p12 := AddCommGroup.add_sub_cancel.symm
    _ = ((endpoint - p14) - p13) - p12 := by rw [h11]

/-- The forced backward value also suffices for the four-part group sum. -/
theorem sufficient {G : Type} [AddCommGroup G] (s p12 p13 p14 endpoint : G)
    (h : s = ((endpoint - p14) - p13) - p12) :
    ((s + p12) + p13) + p14 = endpoint := by
  calc
    ((s + p12) + p13) + p14 =
        (((((endpoint - p14) - p13) - p12) + p12) + p13) + p14 := by rw [h]
    _ = (((endpoint - p14) - p13) + p13) + p14 := by
      rw [AddCommGroup.sub_add_cancel]
    _ = (endpoint - p14) + p14 := by
      rw [AddCommGroup.sub_add_cancel]
    _ = endpoint := AddCommGroup.sub_add_cancel

theorem exact_cut {G : Type} [AddCommGroup G] (s p12 p13 p14 endpoint : G) :
    ((s + p12) + p13) + p14 = endpoint ↔
      s = ((endpoint - p14) - p13) - p12 := by
  exact ⟨necessary s p12 p13 p14 endpoint,
         sufficient s p12 p13 p14 endpoint⟩

#print axioms necessary
#print axioms sufficient
#print axioms exact_cut

end BackwardCut
