import Init

namespace M31ReciprocalWitness

abbrev p : Nat := 2^31 - 1

def liftsAt (a b x y : Nat) : Prop :=
  y^2 % p = (x^3 + a*x + b) % p

/-- Both reciprocal coordinates have signed magnitude a power of two.
Each lifts on the original curve and on the auxiliary curve. -/
theorem smooth_reciprocal_pair :
    let x : Nat := 4
    let u : Nat := 536870912
    x ≠ u ∧ x*u % p = 1 ∧
    min x (p-x) = 2^2 ∧ min u (p-u) = 2^29 ∧
    liftsAt 2 14 x 560044975 ∧ liftsAt 2 14 u 759798956 ∧
    liftsAt 1 0 x 518571843 ∧ liftsAt 1 0 u 435063924 := by
  unfold liftsAt
  decide +kernel

end M31ReciprocalWitness
