import BatchPoint
import Mathlib.Tactic

namespace FourChainWalk

variable {F : Type*} [Field F] [DecidableEq F]

/-- Reverse the four saved chain totals, starting from one inversion. -/
def roots (p : Fin 4 → F) : Fin 4 → F :=
  let ab := p 0 * p 1
  let abc := ab * p 2
  let r := (abc * p 3)⁻¹
  let s := r * p 3
  let t := s * p 2
  ![t * p 1, t * p 0, s * ab, r * abc]

omit [DecidableEq F] in
theorem roots_correct (p : Fin 4 → F) (hp : ∀ i, p i ≠ 0) :
    roots p = fun i => (p i)⁻¹ := by
  funext i
  fin_cases i <;> simp [roots, mul_inv_rev] <;> field_simp [hp]

abbrev Entry (F : Type*) := Fin 4 × BatchPoint.Lane F

/-- Descend while updating the selected product. On return, restore its
previous reciprocal and place the point result in the original position. -/
def scan (A : F) (p : Fin 4 → F) : List (Entry F) → (Fin 4 → F) × List (BatchPoint.Point F)
  | [] => (roots p, [])
  | (g,l) :: rest =>
    let d := BatchPoint.denominator l
    let prod := if d = 0 then p else Function.update p g (p g * d)
    let (back, out) := scan A prod rest
    if d = 0 then (back, BatchPoint.scalar A l :: out)
    else (Function.update back g (back g * d), BatchPoint.applyLane A l (back g * p g) :: out)

theorem scan_correct (A : F) (ls : List (Entry F)) (p : Fin 4 → F) (hp : ∀ i, p i ≠ 0) :
    scan A p ls = (fun i => (p i)⁻¹, ls.map (fun e => BatchPoint.scalar A e.2)) := by
  induction ls generalizing p with
  | nil => simp [scan, roots_correct p hp]
  | cons e es ih =>
    obtain ⟨g,l⟩ := e
    by_cases hz : BatchPoint.denominator l = 0
    · simp [scan, hz, ih p hp]
    · let d := BatchPoint.denominator l
      let q := Function.update p g (p g * d)
      have hq (i) : q i ≠ 0 := by
        by_cases h : i = g
        · subst i; simpa [q, d] using mul_ne_zero (hp g) hz
        · simpa [q, Function.update_of_ne h] using hp i
      have step : (q g)⁻¹ * p g = d⁻¹ := by simp [q, mul_inv_rev, hp]
      have restore : Function.update (fun i => (q i)⁻¹) g ((q g)⁻¹ * d) = fun i => (p i)⁻¹ := by
        funext i
        by_cases h : i = g
        · subst i; simp [q, d, hz, mul_inv_rev, mul_comm]
        · simp [q, Function.update_of_ne h]
      simp only [scan, hz, if_false, List.map_cons]
      change _ = (_, BatchPoint.scalar A l :: _)
      rw [show scan A q es = _ from ih q hq]
      simp only [restore, step, d, BatchPoint.applyLane_correct]

/-- The concrete walk initializes all products to one and assigns slot i to i modulo four. -/
theorem striped_points (A : F) {n : ℕ} (points : Fin n → BatchPoint.Lane F) :
    (scan A (fun _ => 1) (List.ofFn (fun i : Fin n =>
      ((⟨i.val % 4, Nat.mod_lt _ (by decide)⟩ : Fin 4), points i)))).2 =
      List.ofFn (fun i => BatchPoint.scalar A (points i)) := by
  rw [scan_correct _ _ _ (fun _ => one_ne_zero)]
  simp [List.map_ofFn, Function.comp_def]

#print axioms striped_points
end FourChainWalk
