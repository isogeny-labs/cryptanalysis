import Mathlib.Tactic

namespace PublicCosetWalk

variable {G : Type*} [AddCommGroup G]

def initialSegment (t g : G) (n : ℕ) := (List.range n).map fun i => t + i • g

theorem double_segment (t g : G) (n : ℕ) :
    initialSegment t g n ++ (initialSegment t g n).map (· + n • g) = initialSegment t g (n+n) := by
  simp [initialSegment, List.range_add, List.map_map, Function.comp_def, add_smul,
    add_comm, add_left_comm]

def levels (t g : G) : ℕ → List G
  | 0 => [t]
  | k+1 => let prior := levels t g k
           prior ++ prior.map (· + (2^k : ℕ) • g)

theorem ordered_walk (t g : G) (k : ℕ) : levels t g k = initialSegment t g (2^k) := by
  induction k with
  | zero => simp [levels, initialSegment]
  | succ k ih => simpa only [levels, ih, pow_succ, Nat.mul_two] using
                   double_segment t g (2^k)

#print axioms ordered_walk
end PublicCosetWalk
