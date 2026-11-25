import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

namespace M31.ArchiveModularDependencies

/- Row labels follow ArchiveRowDependencies. Each forward proof expresses twice
the desired row equation as an integer combination of the incidence equations. -/
section Rows
variable {K : Type*} [CommRing K] (cancelTwo : ∀ x y : K, 2*x = 2*y → x = y)

include cancelTwo

theorem seed0 (r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 r14 r15 : K) :
    (r6 + r12 = 0 ∧
     r10 = 0 ∧
     -r3 = 0 ∧
     r1 = 0 ∧
     r2 -r13 = 0 ∧
     -r4 + r5 = 0 ∧
     r3 + r13 + r14 = 0 ∧
     -r9 - r11 = 0 ∧
     r11 -r12 - r15 = 0 ∧
     r1 = 0 ∧
     r4 + r14 = 0 ∧
     -r8 + r10 = 0 ∧
     r7 = 0 ∧
     -r6 - r8 = 0 ∧
     r2 + r5 + r9 -r15 = 0 ∧
     -r7 = 0) ↔
    (r1 = 0 ∧
     r2 = r15 ∧
     r3 = 0 ∧
     r4 = r15 ∧
     r5 = r15 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = 0 ∧
     r9 = -r15 ∧
     r10 = 0 ∧
     r11 = r15 ∧
     r12 = 0 ∧
     r13 = r15 ∧
     r14 = -r15) := by
  constructor
  · rintro ⟨h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16⟩
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> apply cancelTwo
    · linear_combination 2 * h4
    · linear_combination h1 + h2 + h3 + h5 - h6 + h7 + h8 + h9 - h11 - h12 + h14 + h15
    · linear_combination -2 * h3
    · linear_combination h1 + h2 - h3 - h5 - h6 - h7 + h8 + h9 + h11 - h12 + h14 + h15
    · linear_combination h1 + h2 - h3 - h5 + h6 - h7 + h8 + h9 + h11 - h12 + h14 + h15
    · linear_combination -2 * h2 + 2 * h12 - 2 * h14
    · linear_combination 2 * h13
    · linear_combination 2 * h2 - 2 * h12
    · linear_combination -2 * h1 - 2 * h2 - 2 * h8 - 2 * h9 + 2 * h12 - 2 * h14
    · linear_combination 2 * h2
    · linear_combination 2 * h1 + 2 * h2 + 2 * h9 - 2 * h12 + 2 * h14
    · linear_combination 2 * h1 + 2 * h2 - 2 * h12 + 2 * h14
    · linear_combination h1 + h2 + h3 - h5 - h6 + h7 + h8 + h9 - h11 - h12 + h14 + h15
    · linear_combination -h1 - h2 + h3 + h5 + h6 + h7 - h8 - h9 + h11 + h12 - h14 - h15
  · rintro ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14⟩
    subst_vars
    repeat' apply And.intro
    all_goals ring

theorem seed1 (r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 r14 : K) :
    (-r1 + (2) * r6 - r13 = 0 ∧
     r5 -r13 = 0 ∧
     r3 = 0 ∧
     r5 -r9 = 0 ∧
     (-2) * r7 -r8 = 0 ∧
     r11 = 0 ∧
     -r3 - r4 = 0 ∧
     -r9 + r12 = 0 ∧
     r10 -r11 - r14 = 0 ∧
     -r8 = 0 ∧
     -r2 - r4 = 0 ∧
     -r1 - r2 + r10 = 0 ∧
     -r12 - r14 = 0) ↔
    (r1 = r14 ∧
     r2 = 0 ∧
     r3 = 0 ∧
     r4 = 0 ∧
     r5 = -r14 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = 0 ∧
     r9 = -r14 ∧
     r10 = r14 ∧
     r11 = 0 ∧
     r12 = -r14 ∧
     r13 = -r14) := by
  constructor
  · rintro ⟨h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13⟩
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> apply cancelTwo
    · linear_combination -2 * h3 + 2 * h6 - 2 * h7 + 2 * h9 + 2 * h11 - 2 * h12
    · linear_combination 2 * h3 + 2 * h7 - 2 * h11
    · linear_combination 2 * h3
    · linear_combination -2 * h3 - 2 * h7
    · linear_combination 2 * h4 - 2 * h8 - 2 * h13
    · linear_combination h1 - h2 - h3 + h4 + h6 - h7 - h8 + h9 + h11 - h12 - h13
    · linear_combination -h5 + h10
    · linear_combination -2 * h10
    · linear_combination -2 * h8 - 2 * h13
    · linear_combination 2 * h6 + 2 * h9
    · linear_combination 2 * h6
    · linear_combination -2 * h13
    · linear_combination -2 * h2 + 2 * h4 - 2 * h8 - 2 * h13
  · rintro ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13⟩
    subst_vars
    repeat' apply And.intro
    all_goals ring

theorem seed2 (r1 r2 r3 r4 r5 r6 r7 r8 r9 : K) :
    (r2 + r9 = 0 ∧
     -r3 = 0 ∧
     r3 -r5 = 0 ∧
     r2 + r6 -r8 = 0 ∧
     -r7 = 0 ∧
     r1 + r4 = 0 ∧
     -r1 - r5 + r7 - r8 = 0 ∧
     r4 + r6 + r9 = 0) ↔
    (r1 = r9 ∧
     r2 = -r9 ∧
     r3 = 0 ∧
     r4 = -r9 ∧
     r5 = 0 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = -r9) := by
  constructor
  · rintro ⟨h1, h2, h3, h4, h5, h6, h7, h8⟩
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> apply cancelTwo
    · linear_combination -h1 + h2 + h3 + h4 - h5 + h6 - h7 - h8
    · linear_combination 2 * h1
    · linear_combination -2 * h2
    · linear_combination h1 - h2 - h3 - h4 + h5 + h6 + h7 + h8
    · linear_combination -2 * h2 - 2 * h3
    · linear_combination -h1 + h2 + h3 + h4 - h5 - h6 - h7 + h8
    · linear_combination -2 * h5
    · linear_combination h1 + h2 + h3 - h4 - h5 - h6 - h7 + h8
  · rintro ⟨e1, e2, e3, e4, e5, e6, e7, e8⟩
    subst_vars
    repeat' apply And.intro
    all_goals ring

end Rows

/-- Multiplication by two is injective for this odd modulus. -/
theorem cancel_group_two (x y : ZMod 2147505293) (h : 2*x = 2*y) : x = y := by
  have inverse : (1073752647 * 2 : ZMod 2147505293) = 1 := by decide
  simpa only [← mul_assoc, inverse, one_mul] using
    congrArg (fun t : ZMod 2147505293 => 1073752647 * t) h

end M31.ArchiveModularDependencies
