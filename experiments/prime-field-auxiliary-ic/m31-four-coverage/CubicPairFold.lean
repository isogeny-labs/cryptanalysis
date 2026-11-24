import Mathlib.Tactic

namespace M31CubicPairFold

abbrev p : Nat := 2147483647
def fold (t : Nat) : Nat :=
  let f := t % (p+1) + t / (p+1)
  if f ≥ p then f-p else f

theorem reduce (t : Nat) (ht : t ≤ p^2+14) :
    t < 2^64 ∧ t % (p+1) + t / (p+1) < 2^32 ∧ fold t = t % p := by
  dsimp [fold, p] at *
  split <;> omega

theorem square_bound {x : Nat} (hx : x < p) : x*x ≤ p^2+14 := by nlinarith

theorem product_bound {s x : Nat} (hs : s < p) (hx : x < p) :
    s+2 < 2^32 ∧ (s+2)*x+14 ≤ p^2+14 := by
  have h := Nat.mul_le_mul (show s+2 ≤ p+1 by omega) (show x ≤ p-1 by omega)
  unfold p at *
  constructor <;> omega

theorem cubic {x : Nat} (hx : x < p) :
    fold ((fold (x*x)+2)*x+14) = ((x*x%p+2)*x+14)%p := by
  rw [(reduce _ (square_bound hx)).2.2]
  exact (reduce _ (product_bound (Nat.mod_lt _ (by decide)) hx).2).2.2

end M31CubicPairFold
