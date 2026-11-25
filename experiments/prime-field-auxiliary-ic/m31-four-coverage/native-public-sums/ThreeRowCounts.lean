import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.List.Sublists

namespace M31.ThreeRowCounts

abbrev F := ZMod 2147505293
abbrev Row := Fin 3 → F

/-- Doubles and both relative signs of each distinct pair, modulo overall sign. -/
def rows : List Row :=
  [![2,0,0], ![0,2,0], ![0,0,2], ![1,1,0], ![1,-1,0],
   ![1,0,1], ![1,0,-1], ![0,1,1], ![0,1,-1]]

def det (a b c : Row) :=
  a 0 * (b 1*c 2 - b 2*c 1) - a 1 * (b 0*c 2 - b 2*c 0) +
  a 2 * (b 0*c 1 - b 1*c 0)

def occupied (rs : List Row) (j : Fin 3) : Bool := rs.any fun a => a j != 0

def singular : List Row → Bool
  | [a,b,c] => det a b c == 0
  | _ => false

def triples := (rows.sublistsLen 3).filter singular

-- Fix the first two vertices for the two-vertex count; use all three for the other.
theorem local_counts :
    (triples.filter (fun t => occupied t 0 && occupied t 1 && !occupied t 2)).length = 4 ∧
    (triples.filter (fun t => occupied t 0 && occupied t 1 && occupied t 2)).length = 4 := by
  decide +kernel

/-- A coordinate appearing in just one row rules out a dependency in which
all three coefficients are nonzero. -/
theorem no_private_coordinate {K : Type*} [Field K] (u v w a : K)
    (hu : u ≠ 0) (ha : a ≠ 0) : u*a + v*0 + w*0 ≠ 0 := by
  simpa only [mul_zero, add_zero] using mul_ne_zero hu ha

/-- Three rows involving at most two vertices each can cover at most three
vertices if every occupied vertex occurs in at least two rows. -/
theorem support_bound {V : Type*} [DecidableEq V] (s a b c : Finset V)
    (ha : a ⊆ s) (hb : b ⊆ s) (hc : c ⊆ s)
    (sa : a.card ≤ 2) (sb : b.card ≤ 2) (sc : c.card ≤ 2)
    (twice : ∀ x ∈ s, 2 ≤ (if x ∈ a then 1 else 0) +
        (if x ∈ b then 1 else 0) + (if x ∈ c then 1 else (0 : ℕ))) : s.card ≤ 3 := by
  have count (t : Finset V) (ht : t ⊆ s) :
      (∑ x ∈ s, if x ∈ t then 1 else (0 : ℕ)) = t.card := by
    rw [Finset.sum_boole, Finset.filter_mem_eq_inter, Finset.inter_eq_right.mpr ht]
    rfl
  have h := Finset.sum_le_sum twice
  simp only [Finset.sum_const, nsmul_eq_mul, Nat.cast_id, Finset.sum_add_distrib,
    count a ha, count b hb, count c hc] at h
  omega

theorem totals :
    4 * Nat.choose 17 2 + 4 * Nat.choose 17 3 = 3264 ∧ Nat.choose 289 3 = 3981264 := by
  decide +kernel

end M31.ThreeRowCounts
