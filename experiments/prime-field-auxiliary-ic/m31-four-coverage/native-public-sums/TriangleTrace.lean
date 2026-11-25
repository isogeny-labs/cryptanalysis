import Mathlib

namespace TriangleTrace

variable {V : Type*} [Fintype V]

def total (f : V → V → V → ℤ) := ∑ i, ∑ j, ∑ k, f i j k

private theorem swap12 (f : V → V → V → ℤ) : total (fun i j k => f j i k) = total f :=
  Finset.sum_comm

private theorem swap23 (f : V → V → V → ℤ) : total (fun i j k => f i k j) = total f :=
  Finset.sum_congr rfl (fun _ _ => Finset.sum_comm)

variable [LinearOrder V]

def increasing (B : Matrix V V ℤ) (i j k : V) :=
  if i < j ∧ j < k then B i j * B j k * B k i else 0

theorem cubic_trace (B : Matrix V V ℤ) (sym : ∀ i j, B i j = B j i)
    (diag : ∀ i, B i i = 0) :
    (B * B * B).trace = 6 * total (increasing B) := by
  let f := increasing B
  have part (i j k : V) : B i j * B j k * B k i =
      f i j k + f j i k + f i k j + f j k i + f k i j + f k j i := by
    dsimp only [f, increasing]
    have sij := sym j i
    have sik := sym k i
    have sjk := sym k j
    rcases lt_trichotomy i j with h|h|h <;>
      rcases lt_trichotomy j k with g|g|g <;>
      rcases lt_trichotomy i k with e|e|e <;> grind
  have expand : (B * B * B).trace = total (fun i j k => B i k * B k j * B j i) := by
    simp [Matrix.trace, Matrix.diag, Matrix.mul_apply, Finset.sum_mul, total]
  rw [expand, swap23 (fun i j k => B i j * B j k * B k i)]
  simp_rw [part]
  have t (a b : V → V → V → ℤ) : total (fun i j k => a i j k + b i j k) = total a + total b := by
    simp only [total, Finset.sum_add_distrib]
  have rot := (swap12 (fun i j k => f i k j)).trans (swap23 f)
  have revrot := (swap23 (fun i j k => f j i k)).trans (swap12 f)
  have rev := (swap12 (fun i j k => f k i j)).trans revrot
  simp only [t]
  rw [swap12 f, swap23 f, rot, revrot, rev]
  ring

/-- A triangle whose three overlaps use the same line has weight one for
any signs on its three incidences. -/
theorem same_line (x y z : ℤ) (hx : x^2 = 1) (hy : y^2 = 1) (hz : z^2 = 1) :
    (x*y)*(y*z)*(z*x) = 1 := by
  calc
    _ = x^2*y^2*z^2 := by ring
    _ = 1 := by rw [hx, hy, hz]; decide

/-- Convert a signed triangle sum into a count of its positive terms. -/
theorem signed_sum {α : Type*} (s : Finset α) (w : α → ℤ)
    (h : ∀ a ∈ s, w a = 1 ∨ w a = -1) :
    ∑ a ∈ s, w a = 2 * ((s.filter (fun a => w a = 1)).card : ℤ) - s.card := by
  classical
  induction s using Finset.induction_on with
  | empty => simp
  | insert a s ha ih =>
    have hs := ih (fun x hx => h x (Finset.mem_insert_of_mem hx))
    rcases h a (Finset.mem_insert_self _ _) with hp|hp <;>
      simp [Finset.filter_insert, ha, hp, hs, Finset.notMem_mono (Finset.filter_subset _ _) ha] <;> omega

#print axioms cubic_trace
#print axioms signed_sum
end TriangleTrace
