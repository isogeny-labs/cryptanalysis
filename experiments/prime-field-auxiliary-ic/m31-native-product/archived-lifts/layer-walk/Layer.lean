import Mathlib.Tactic

namespace M31Layer

variable {G : Type*} [AddCommGroup G]

def expand (t g : G) : ℕ → List G
  | 0 => [t]
  | k+1 =>
    let xs := expand t g k
    xs ++ xs.map (· + (2^k : ℕ) • g)

theorem ordered (t g : G) (k : ℕ) :
    expand t g k = (List.range (2^k)).map (fun i => t + i • g) := by
  induction k with
  | zero => simp [expand, List.range_one]
  | succ k ih =>
    simp only [expand, ih, pow_succ, Nat.mul_two, List.range_add,
      List.map_append, List.map_map]
    congr 1
    apply List.map_congr_left
    intro i _
    simp [add_nsmul, add_comm, add_assoc]

theorem reverse_step {F : Type*} [Field F] (a d n : F) (ha : a ≠ 0) (hd : d ≠ 0) :
    n * a * (a*d)⁻¹ = n/d ∧ (a*d)⁻¹ * d = a⁻¹ := by
  constructor <;> field_simp

/-- k+1 expansion layers use k+1 product inversions and k stride doublings.
    The final midpoint check adds one affine inversion. -/
theorem half_walk_savings (k : ℕ) (hk : 3 ≤ k) :
    (k+1) + k + 1 < 2^(k+1) := by
  induction k, hk using Nat.le_induction with
  | base => decide
  | succ k _ ih =>
    rw [pow_succ (2 : ℕ) (k+1)]
    omega

end M31Layer
