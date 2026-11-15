import Mathlib.Data.Real.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic.Ring

/-!
A height-to-coordinate coercivity condition and a basis-conditioning
counterexample for the finite lattice step in the xedni analysis.
-/

namespace XedniBasisCoercivity

/-- A quantitative lower bound on the height of each coordinate gives an
integer coordinate box from an upper height bound. The same `μ` must hold
for the selected basis and all represented points under consideration. -/
theorem coordinate_bounded_of_height {d : ℕ}
    (a : Fin d → ℤ) (height μ B : ℝ) (K : ℕ)
    (hμ : 0 < μ) (hheight : height ≤ B)
    (hcoercive : ∀ i, μ * ((a i).natAbs : ℝ) ^ 2 ≤ height)
    (hthreshold : B < μ * ((K + 1 : ℕ) : ℝ) ^ 2) :
    ∀ i, (a i).natAbs ≤ K := by
  intro i
  by_contra hnot
  have hn : K + 1 ≤ (a i).natAbs := by omega
  have hr : ((K + 1 : ℕ) : ℝ) ≤ ((a i).natAbs : ℝ) := by
    exact_mod_cast hn
  have hs : (((K + 1 : ℕ) : ℝ) ^ 2) ≤ (((a i).natAbs : ℝ) ^ 2) := by
    exact pow_le_pow_left₀ (Nat.cast_nonneg _) hr 2
  have hm := mul_le_mul_of_nonneg_left hs (le_of_lt hμ)
  have hcontr : μ * ((K + 1 : ℕ) : ℝ) ^ 2 ≤ B :=
    (hm.trans (hcoercive i)).trans hheight
  exact (not_lt_of_ge hcontr) hthreshold

/-- A unimodular shear of the integer lattice. -/
def shear (N : ℕ) (a : ℤ × ℤ) : ℤ × ℤ :=
  (a.1 + (N : ℤ) * a.2, a.2)

def unshear (N : ℕ) (v : ℤ × ℤ) : ℤ × ℤ :=
  (v.1 - (N : ℤ) * v.2, v.2)

theorem unshear_shear (N : ℕ) (a : ℤ × ℤ) :
    unshear N (shear N a) = a := by
  cases a with
  | mk x y =>
    simp [shear, unshear]

theorem shear_unshear (N : ℕ) (v : ℤ × ℤ) :
    shear N (unshear N v) = v := by
  cases v with
  | mk x y =>
    simp [shear, unshear]

theorem shear_add (N : ℕ) (a b : ℤ × ℤ) :
    shear N (a + b) = shear N a + shear N b := by
  cases a with
  | mk x y =>
    cases b with
    | mk z w =>
      ext <;> simp [shear, mul_add] <;> ring

/-- The shear is a change of basis of the full integer lattice. -/
def shearAddEquiv (N : ℕ) : (ℤ × ℤ) ≃+ (ℤ × ℤ) where
  toFun := shear N
  invFun := unshear N
  left_inv := unshear_shear N
  right_inv := shear_unshear N
  map_add' := shear_add N

/-- Standard squared Euclidean height on the integer lattice. -/
def squareHeight (v : ℤ × ℤ) : ℕ :=
  v.1.natAbs ^ 2 + v.2.natAbs ^ 2

theorem squareHeight_pos_of_ne_zero (v : ℤ × ℤ) (hv : v ≠ (0, 0)) :
    0 < squareHeight v := by
  by_cases h1 : v.1 = 0
  · have h2 : v.2 ≠ 0 := by
      intro h2
      exact hv (Prod.ext h1 h2)
    have hp : 0 < v.2.natAbs := Int.natAbs_pos.mpr h2
    simpa [squareHeight, h1] using (pow_pos hp 2)
  · have hp : 0 < v.1.natAbs := Int.natAbs_pos.mpr h1
    have hp2 : 0 < v.1.natAbs ^ 2 := pow_pos hp 2
    exact lt_of_lt_of_le hp2 (Nat.le_add_right _ _)

/-- Even with fixed minimum positive height one, a change of integer basis
can make the coordinate of a unit-height vector exceed any proposed bound. -/
theorem unbounded_coordinates_in_sheared_basis (C : ℕ) :
    ∃ N : ℕ,
      squareHeight ((0 : ℤ), (1 : ℤ)) = 1 ∧
      shear N (unshear N ((0 : ℤ), (1 : ℤ))) = ((0 : ℤ), (1 : ℤ)) ∧
      C < (unshear N ((0 : ℤ), (1 : ℤ))).1.natAbs := by
  refine ⟨C + 1, by simp [squareHeight], shear_unshear _ _, ?_⟩
  simp only [unshear]
  omega

end XedniBasisCoercivity

#print axioms XedniBasisCoercivity.coordinate_bounded_of_height
#print axioms XedniBasisCoercivity.unshear_shear
#print axioms XedniBasisCoercivity.shear_unshear
#print axioms XedniBasisCoercivity.shear_add
#print axioms XedniBasisCoercivity.shearAddEquiv
#print axioms XedniBasisCoercivity.squareHeight_pos_of_ne_zero
#print axioms XedniBasisCoercivity.unbounded_coordinates_in_sheared_basis
