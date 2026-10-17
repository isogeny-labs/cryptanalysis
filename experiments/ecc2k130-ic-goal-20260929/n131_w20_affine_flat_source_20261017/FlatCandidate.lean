import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace FlatCandidate

/-- A translation `w` is admissible when every point in a finite affine flat
remains in the source-valid set after translation. -/
def candidate {R : Type} [CommRing R]
    (valid : R → Prop) (base : R) (offsets : List R) (w : R) : Prop :=
  ∀ s ∈ offsets, valid (base + s + w)

def extend {R : Type} [CommRing R] (offsets : List R) (v : R) : List R :=
  offsets ++ offsets.map (fun s => s + v)

/-- The candidate set for an extended flat is the intersection of the
previous candidate set and its translate by the new direction. -/
theorem candidate_extend {R : Type} [CommRing R]
    (valid : R → Prop) (base : R) (offsets : List R) (v w : R) :
    candidate valid base (extend offsets v) w ↔
      candidate valid base offsets w ∧ candidate valid base offsets (v + w) := by
  constructor
  · intro h
    constructor
    · intro s hs
      exact h s (by simp [extend, hs])
    · intro s hs
      have hm : s + v ∈ offsets.map (fun u => u + v) :=
        List.mem_map.mpr ⟨s, hs, rfl⟩
      have hext : s + v ∈ extend offsets v :=
        List.mem_append.mpr (Or.inr hm)
      have hv : valid (base + (s + v) + w) := h (s + v) hext
      have heq : base + (s + v) + w = base + s + (v + w) := by grind
      rw [heq] at hv
      exact hv
  · rintro ⟨ha, hb⟩ s hs
    have hm : s ∈ offsets ∨ s ∈ offsets.map (fun u => u + v) := by
      simpa [extend] using hs
    rcases hm with hleft | hright
    · exact ha s hleft
    · obtain ⟨u, hu, hEq⟩ := List.mem_map.mp hright
      subst s
      have hv := hb u hu
      have heq : base + (u + v) + w = base + u + (v + w) := by grind
      rw [heq]
      exact hv

#print axioms candidate_extend

end FlatCandidate
