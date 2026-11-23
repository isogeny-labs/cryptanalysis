import Std

namespace M31TwistBand

structure Band where
  prime : Nat
  original : Nat
  twist : Nat

/-- Counts from the PARI enumeration in twist_counts.gp. To reproduce the
finer partition, use its definitions and run
`for(i=1,#oddPrimes, enumerate(1,1,oddPrimes[i]); print(counts))`.
Difference successive cumulative vectors (starting from zero); original is
the sum of cells 3 and 4, twist the sum of cells 2 and 4. -/
def bands : List Band :=
  [⟨3,74,84⟩, ⟨5,461,472⟩, ⟨7,1983,1961⟩, ⟨11,4986,4959⟩,
   ⟨13,11148,11113⟩, ⟨17,20162,20105⟩, ⟨19,33710,33662⟩,
   ⟨23,50335,50545⟩, ⟨29,68548,68657⟩, ⟨31,93422,92879⟩,
   ⟨37,116351,116607⟩, ⟨41,142572,143158⟩, ⟨43,175324,175822⟩,
   ⟨47,206322,206690⟩]

def count (useTwist : Nat → Bool) (rows : List Band) : Nat :=
  (rows.map fun b => if useTwist b.prime then b.twist else b.original).sum

theorem count_le (useTwist : Nat → Bool) (rows : List Band) :
    count useTwist rows ≤ (rows.map fun b => max b.original b.twist).sum := by
  induction rows with
  | nil => exact Nat.le_refl 0
  | cons b bs ih =>
    simp only [count, List.map_cons, List.sum_cons] at *
    apply Nat.add_le_add _ ih
    split
    · exact Nat.le_max_right ..
    · exact Nat.le_max_left ..

theorem ceiling (useTwist : Nat → Bool) : count useTwist bands ≤ 927446 :=
  count_le useTwist bands

theorem attained :
    count (fun p => [3,5,23,29,37,41,43,47].contains p) bands = 927446 := by decide

theorem fixedCounts :
    count (fun _ => false) bands = 925398 ∧
    count (fun _ => true) bands = 926714 := by decide

end M31TwistBand
