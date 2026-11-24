import Mathlib

namespace PrefixInverse

variable {F : Type*} [Field F]

/-- Save each prefix on descent. On return multiply the reciprocal by the
saved prefix to emit the next inverse, and by the input to undo that step. -/
def root (p : F) : List F → F × List F
  | [] => (p⁻¹, [])
  | x :: xs =>
    let (r, ys) := root (p*x) xs
    (r*x, (p*r)::ys)

theorem root_correct (p : F) (xs : List F) (hp : p ≠ 0) (hx : ∀ x ∈ xs, x ≠ 0) :
    root p xs = (p⁻¹, xs.map (·⁻¹)) := by
  induction xs generalizing p with
  | nil => rfl
  | cons x xs ih =>
    have hn := hx x (by simp)
    simp only [root, ih (p*x) (mul_ne_zero hp hn) (fun a ha => hx a (by simp [ha])),
      List.map_cons, Prod.mk.injEq, List.cons.injEq, and_true]
    constructor <;> field_simp

def invertRoots {n : ℕ} (v : Fin n → F) : Fin n → F :=
  let roots := (root 1 (List.ofFn v)).2
  fun j => roots[j.val]?.getD 0

theorem roots_correct {n : ℕ} (v : Fin n → F) (hv : ∀ i, v i ≠ 0) (j : Fin n) :
    invertRoots v j = (v j)⁻¹ := by
  unfold invertRoots
  rw [root_correct _ _ one_ne_zero (by simpa using hv)]
  simp [j.isLt]

/-- Each entry carries its lane index. A cyclic schedule is one instance;
the list order records the original interleaving, including partial blocks. -/
def sweep {n : ℕ} (v : Fin n → F) : List (Fin n × F) → (Fin n → F) × List F
  | [] => (invertRoots v, [])
  | (i,x) :: xs =>
    let (r, ys) := sweep (Function.update v i (v i*x)) xs
    (Function.update r i (r i*x), (v i*r i)::ys)

theorem sweep_correct {n : ℕ} (v : Fin n → F) (xs : List (Fin n × F))
    (hv : ∀ i, v i ≠ 0) (hx : ∀ e ∈ xs, e.2 ≠ 0) :
    sweep v xs = (fun i => (v i)⁻¹, xs.map (fun e => e.2⁻¹)) := by
  induction xs generalizing v with
  | nil =>
    exact Prod.ext (funext (roots_correct v hv)) rfl
  | cons e xs ih =>
    obtain ⟨i,x⟩ := e
    have hn : x ≠ 0 := hx (i,x) (by simp)
    have hu : ∀ j, Function.update v i (v i*x) j ≠ 0 := by
      intro j
      by_cases h : j = i
      · subst j; simpa using mul_ne_zero (hv i) hn
      · simpa [Function.update_of_ne h] using hv j
    simp only [sweep, ih _ hu (fun a ha => hx a (by simp [ha])), List.map_cons,
      Function.update_self, Prod.mk.injEq, List.cons.injEq, and_true]
    constructor
    · funext j
      by_cases h : j = i
      · subst j; simp only [Function.update_self]; field_simp [hn, hv i]
      · simp [Function.update_of_ne h]
    · field_simp [hv i, hn]

#print axioms sweep_correct
end PrefixInverse
