import Std.Tactic
import Init.Grind.Ring.Basic
set_option autoImplicit false

namespace LPProjection
open Lean.Grind

/-- Known alternating cancellation, including the final edge. -/
theorem even_four_cycle {K : Type} [CommRing K] (a b c d : K) :
    ((a + b) - (b + c)) + ((c + d) - (d + a)) = 0 := by
  grind

/-- A single odd cycle leaves twice its root; it is not a constraint alone. -/
theorem odd_triangle {K : Type} [CommRing K] (a b c : K) :
    ((a + b) - (b + c)) + (c + a) = 2 * a := by
  grind

/-- Two odd cycles based at the same vertex give a cancellation. -/
theorem two_odd_triangles {K : Type} [CommRing K] (a b c d e : K) :
    (((a + b) - (b + c)) + (c + a)) -
      (((a + d) - (d + e)) + (e + a)) = 0 := by
  grind

theorem half_ground_edge {K : Type} [CommRing K] (a b : K) :
    2 * (a + b) - 2 * a = 2 * b := by
  grind

def dot {C K : Type} [CommRing K] (columns : List C) (r v : C → K) : K :=
  match columns with
  | [] => 0
  | c :: cs => r c * v c + dot cs r v

def combine {I C K : Type} [CommRing K]
    (indices : List I) (coefficient : I → K) (vectors : I → C → K) : C → K :=
  fun c => match indices with
  | [] => 0
  | i :: tail => coefficient i * vectors i c + combine tail coefficient vectors c

theorem dot_zero {C K : Type} [CommRing K] (columns : List C) (r : C → K) :
    dot columns r (fun _ => 0) = 0 := by
  induction columns with
  | nil => rfl
  | cons c cs ih => simp only [dot, ih]; grind

theorem dot_add {C K : Type} [CommRing K]
    (columns : List C) (r v w : C → K) :
    dot columns r (fun c => v c + w c) = dot columns r v + dot columns r w := by
  induction columns with
  | nil => simp only [dot]; grind
  | cons c cs ih => simp only [dot, ih]; grind

theorem dot_scale {C K : Type} [CommRing K]
    (columns : List C) (r v : C → K) (s : K) :
    dot columns r (fun c => s * v c) = s * dot columns r v := by
  induction columns with
  | nil => simp only [dot]; grind
  | cons c cs ih => simp only [dot, ih]; grind

def RowKernel {R C K : Type} [CommRing K]
    (columns : List C) (matrix : R → C → K) (v : C → K) : Prop :=
  ∀ row, dot columns (matrix row) v = 0

def FullKernel {R LP FB K : Type} [CommRing K]
    (lpcols : List LP) (fbcols : List FB)
    (left : R → LP → K) (right : R → FB → K)
    (lp : LP → K) (fb : FB → K) : Prop :=
  ∀ row, dot lpcols (left row) lp + dot fbcols (right row) fb = 0

theorem combine_kernel {I R C K : Type} [CommRing K]
    (columns : List C) (matrix : R → C → K)
    (indices : List I) (coefficient : I → K) (vectors : I → C → K)
    (valid : ∀ i, RowKernel columns matrix (vectors i)) :
    RowKernel columns matrix (combine indices coefficient vectors) := by
  induction indices with
  | nil => intro row; exact dot_zero columns (matrix row)
  | cons i tail ih =>
    intro row
    change dot columns (matrix row)
      (fun c => coefficient i * vectors i c + combine tail coefficient vectors c) = 0
    rw [dot_add, dot_scale, valid i row, ih row]
    grind

theorem combine_full_kernel {I R LP FB K : Type} [CommRing K]
    (lpcols : List LP) (fbcols : List FB)
    (left : R → LP → K) (right : R → FB → K)
    (indices : List I) (coefficient : I → K)
    (lifts : I → LP → K) (images : I → FB → K)
    (valid : ∀ i, FullKernel lpcols fbcols left right (lifts i) (images i)) :
    FullKernel lpcols fbcols left right
      (combine indices coefficient lifts) (combine indices coefficient images) := by
  induction indices with
  | nil =>
    intro row
    change dot lpcols (left row) (fun _ => 0) + dot fbcols (right row) (fun _ => 0) = 0
    rw [dot_zero, dot_zero]
    grind
  | cons i tail ih =>
    intro row
    change dot lpcols (left row)
      (fun c => coefficient i * lifts i c + combine tail coefficient lifts c) +
      dot fbcols (right row)
      (fun c => coefficient i * images i c + combine tail coefficient images c) = 0
    rw [dot_add, dot_scale, dot_add, dot_scale]
    have head := valid i row
    have rest := ih row
    grind

/-- Conditional finite certificate bridge. The forward direction needs a
complete full-kernel projection span and every projected generator in ker(C).
The reverse direction needs a complete ker(C) span and valid full lifts.
No numerical matrix, computed basis completeness, field character, or program
correctness is supplied by this generic theorem. -/
theorem projected_kernel_iff_of_finite_spans
    {I J R S LP FB K : Type} [CommRing K]
    (lpcols : List LP) (fbcols : List FB)
    (left : R → LP → K) (right : R → FB → K) (constraints : S → FB → K)
    (fullIndices : List I) (fullImages : I → FB → K)
    (imageIndices : List J) (lifts : J → LP → K) (images : J → FB → K)
    (fullSpan : ∀ lp fb, FullKernel lpcols fbcols left right lp fb →
      ∃ coefficient, combine fullIndices coefficient fullImages = fb)
    (annihilated : ∀ i, RowKernel fbcols constraints (fullImages i))
    (constraintSpan : ∀ fb, RowKernel fbcols constraints fb →
      ∃ coefficient, combine imageIndices coefficient images = fb)
    (validLifts : ∀ j, FullKernel lpcols fbcols left right (lifts j) (images j))
    (fb : FB → K) :
    RowKernel fbcols constraints fb ↔ ∃ lp, FullKernel lpcols fbcols left right lp fb := by
  constructor
  · intro h
    obtain ⟨coefficient, sectionEq⟩ := constraintSpan fb h
    have lifted := combine_full_kernel lpcols fbcols left right imageIndices
      coefficient lifts images validLifts
    rw [sectionEq] at lifted
    exact ⟨combine imageIndices coefficient lifts, lifted⟩
  · rintro ⟨lp, h⟩
    obtain ⟨coefficient, sectionEq⟩ := fullSpan lp fb h
    have constrained := combine_kernel fbcols constraints fullIndices
      coefficient fullImages annihilated
    rw [sectionEq] at constrained
    exact constrained

end LPProjection
