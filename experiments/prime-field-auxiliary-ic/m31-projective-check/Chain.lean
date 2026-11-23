import Mathlib.Tactic

namespace PublicChain
variable {F : Type*} [Field F] [DecidableEq F]

structure Step (F : Type*) where
  r : F
  a : F
  b : F

def affine (s : Step F) (x : F) : Option F :=
  let u := x - s.r
  if u = 0 then none else some (u + s.a + s.b / u)

def project (s : Step F) (z : F × F) : F × F :=
  let u := z.1 - s.r * z.2
  (u*u + s.a*(u*z.2) + s.b*(z.2*z.2), u*z.2)

def Represents (z : F × F) : Option F → Prop
  | none => z.2 = 0
  | some x => z.2 ≠ 0 ∧ z.1 = x * z.2

theorem step_correct (s : Step F) (z : F × F) (v : Option F) (h : Represents z v) :
    Represents (project s z) (v.bind (affine s)) := by
  cases v with
  | none =>
    change z.2 = 0 at h
    simp [Represents, project, h]
  | some x =>
    obtain ⟨hd, hn⟩ := h
    have hu : z.1 - s.r*z.2 = (x-s.r)*z.2 := by rw [hn]; ring
    by_cases hp : x-s.r = 0
    · simp [Represents, project, affine, hu, hp]
    · simp only [Option.bind_some, affine, hp, ↓reduceIte, Represents, project, hu]
      constructor
      · exact mul_ne_zero (mul_ne_zero hp hd) hd
      · field_simp [hp]

theorem chain_correct (steps : List (Step F)) (z : F × F) (v : Option F)
    (h : Represents z v) :
    Represents (steps.foldl (fun acc s => project s acc) z)
      (steps.foldl (fun acc s => acc.bind (affine s)) v) := by
  induction steps generalizing z v with
  | nil => exact h
  | cons s rest ih => exact ih _ _ (step_correct s z v h)

omit [DecidableEq F] in
theorem terminal (z : F × F) (v : Option F) (c : F) (h : Represents z v) :
    (z.2 ≠ 0 ∧ z.1 = c*z.2) ↔ v = some c := by
  cases v with
  | none =>
    change z.2 = 0 at h
    simp [h]
  | some x =>
    obtain ⟨hd, hn⟩ := h
    simp [hd, hn]

theorem check_correct (steps : List (Step F)) (x c : F) :
    let z := steps.foldl (fun acc s => project s acc) (x, 1)
    (z.2 ≠ 0 ∧ z.1 = c*z.2) ↔
      steps.foldl (fun acc s => acc.bind (affine s)) (some x) = some c := by
  exact terminal _ _ c (chain_correct steps (x, 1) (some x) (by simp [Represents]))

#print axioms check_correct
#print axioms chain_correct
#print axioms terminal
end PublicChain
