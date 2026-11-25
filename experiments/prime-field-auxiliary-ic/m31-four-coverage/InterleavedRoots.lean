import FiberLift

namespace M31InterleavedRoots
open M31FiberLift

abbrev Block := Nat → Fin 4 → F31

/-- One round of the inner chain loop. A store changes all four lanes of one register. -/
def sweep (state : Block) : Nat → Block
  | 0 => state
  | n+1 => fun b k =>
    if b = n then (sweep state n b k)^2 else sweep state n b k

theorem sweep_prefix (state : Block) (n b : Nat) (k : Fin 4) :
    sweep state n b k = if b < n then (state b k)^2 else state b k := by
  induction n with
  | zero => simp [sweep]
  | succ n ih =>
    by_cases e : b = n
    · subst b
      simp [sweep, ih]
    · have h : b < n + 1 ↔ b < n := by omega
      simp [sweep, e, ih, h]

def rounds (width : Nat) (initial : Block) : Nat → Block
  | 0 => initial
  | t+1 => sweep (rounds width initial t) width

theorem round_value (width : Nat) (initial : Block) (t b : Nat)
    (hb : b < width) (k : Fin 4) :
    rounds width initial t b k = squares (initial b) t k := by
  induction t with
  | zero => rfl
  | succ t ih => simp [rounds, sweep_prefix, hb, squares, ih]

def load (xs : Nat → F31) (base : Nat) : Block := fun b k =>
  let x := xs (base + 4*b + k.val)
  x * (x*x + 1)

/-- At any offset of a complete block, the validation test accepts exactly
the liftable x values at that same flat input offset, including rhs zero. -/
theorem flat_accept (xs : Nat → F31) (base width j : Nat) (hj : j < 4*width) :
    let x := xs (base+j)
    let k : Fin 4 := ⟨j%4, Nat.mod_lt _ (by decide)⟩
    (rounds width (load xs base) 29 (j/4) k)^2 = x*(x*x+1) ↔
      ∃ y : F31, y^2 = x^3+x := by
  dsimp only
  have hb : j/4 < width := by omega
  have idx : base + 4*(j/4) + j%4 = base+j := by omega
  rw [round_value _ _ _ _ hb]
  let k : Fin 4 := ⟨j%4, Nat.mod_lt _ (by decide)⟩
  have h := lift_exact (load xs base (j/4)) k
  have v : load xs base (j/4) k = xs (base+j)*(xs (base+j)*xs (base+j)+1) := by
    simp [load, k, idx]
  rw [v] at h
  have cubic (a : F31) : a*(a*a+1) = a^3+a := by ring
  simpa only [cubic] using h

end M31InterleavedRoots
