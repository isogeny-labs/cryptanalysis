import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace SiblingCheck

variable {K : Type*} [Field K] [DecidableEq K]

structure Step (K : Type*) where
  r : K
  a : K
  b : K

def image (s : Step K) (x : K) : Option K :=
  if x = s.r then none else some ((x-s.r) + s.a + s.b/(x-s.r))

def parent (s : Step K) (pair : K × K) := (pair.1-s.r) + s.a + (pair.2-s.r)

theorem merge (s : Step K) (pair : K × K) (hb : s.b ≠ 0)
    (huv : (pair.1-s.r)*(pair.2-s.r) = s.b) :
    image s pair.1 = some (parent s pair) ∧ image s pair.2 = some (parent s pair) := by
  have h := mul_ne_zero_iff.mp (huv ▸ hb : (pair.1-s.r)*(pair.2-s.r) ≠ 0)
  have hl := sub_ne_zero.mp h.1
  have hr := sub_ne_zero.mp h.2
  simp only [image, hl, hr, ↓reduceIte, parent, Option.some.injEq]
  constructor <;> (rw [← huv]; field_simp [h.1,h.2]; all_goals ring)

def follow : List (Step K) → K → Option K
  | [], x => some x
  | s::ss, x => (image s x).bind (follow ss)

/-- Every input is accounted for in a checked pair, and the resulting
parent list is itself certified against the remaining maps. -/
def certified : List (Step K) → List K → K → Prop
  | [], xs, c => xs = [c]
  | s::ss, xs, c => ∃ pairs : List (K × K),
      s.b ≠ 0 ∧ (∀ x ∈ xs, ∃ z ∈ pairs, x = z.1 ∨ x = z.2) ∧
      (∀ z ∈ pairs, (z.1-s.r)*(z.2-s.r) = s.b) ∧
      certified ss (pairs.map (parent s)) c

theorem sound (steps : List (Step K)) (xs : List K) (c : K)
    (h : certified steps xs c) : ∀ x ∈ xs, follow steps x = some c := by
  induction steps generalizing xs with
  | nil =>
    change xs = [c] at h
    simp [h, follow]
  | cons s ss ih =>
    obtain ⟨pairs, hb, covers, product, next⟩ := h
    intro x hx
    obtain ⟨z,hz,hx'⟩ := covers x hx
    have m := merge s z hb (product z hz)
    have hp := ih _ next (parent s z) (List.mem_map_of_mem hz)
    rcases hx' with rfl | rfl
    · simpa [follow,m.1] using hp
    · simpa [follow,m.2] using hp

end SiblingCheck
#print axioms SiblingCheck.sound
