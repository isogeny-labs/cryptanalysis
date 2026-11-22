import Mathlib.Data.Fintype.Card
import Mathlib.Tactic

namespace BooleanRectangles

/-- A rectangle covering two distinct diagonal entries of the identity
also covers an off-diagonal entry. -/
theorem identity_bound {n r : Nat} (A B : Fin r → Fin n → Prop)
    (exactCover : ∀ i j, (∃ t, A t i ∧ B t j) ↔ i = j) : n ≤ r := by
  classical
  have diag (i : Fin n) := (exactCover i i).mpr rfl
  choose label left right using diag
  have inj : Function.Injective label := by
    intro i j e
    exact (exactCover i j).mp ⟨label i, left i, e ▸ right j⟩
  simpa using Fintype.card_le_of_injective label inj

variable {F : Type*} [Field F]
def rhs (x : F) := x^3+2*x+14
def middle (x z : F) := (x+z)*(x*z+2)+28
def constantTerm (x z : F) := (x*z-2)^2-56*(x+z)
def quad (x z t : F) := (x-z)^2*t^2-2*middle x z*t+constantTerm x z

theorem permute (x z t : F) : quad x z t = quad x t z := by
  unfold quad middle constantTerm
  ring

theorem discriminantIdentity (x z : F) :
    middle x z ^ 2 - (x-z)^2*constantTerm x z = 4*rhs x*rhs z := by
  unfold middle constantTerm rhs
  ring

theorem hasRoot (x z u v : F) (distinct : x ≠ z)
    (hx : u^2 = rhs x) (hz : v^2 = rhs z) :
    quad x z ((middle x z - 2*u*v)/(x-z)^2) = 0 := by
  have h := discriminantIdentity x z
  rw [← hx, ← hz] at h
  unfold quad
  field_simp [sub_ne_zero.mpr distinct]
  linear_combination -h

theorem equal_middle (z : F) : middle z z = 2*rhs z := by
  unfold middle rhs
  ring

/-- The x-coordinate obtained from the secant slope equals the root above. -/
theorem secant_root (x z u v : F) (distinct : x ≠ z)
    (hx : u^2 = rhs x) (hz : v^2 = rhs z) :
    ((u-v)/(x-z))^2-x-z = (middle x z-2*u*v)/(x-z)^2 := by
  unfold middle
  unfold rhs at hx hz
  field_simp [sub_ne_zero.mpr distinct]
  linear_combination hx + hz

/-- Count nonempty rows when each contributing rectangle covers at most b rows. -/
theorem cover_size {R I : Type*} [DecidableEq R] (active : Finset R)
    (indices : Finset I) (rows : I → Finset R) (b : Nat)
    (covered : active ⊆ indices.biUnion rows)
    (bound : ∀ t ∈ indices, (rows t).card ≤ b) :
    active.card ≤ indices.card * b :=
  (Finset.card_le_card covered).trans (Finset.card_biUnion_le_card_mul _ _ _ bound)

example (r : Nat) (h : 1073752645 ≤ r*64) : 16777386 ≤ r := by omega

#print axioms identity_bound
#print axioms hasRoot
end BooleanRectangles
