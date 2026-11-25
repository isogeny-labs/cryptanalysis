import SignedBall
import Mathlib.Tactic

namespace M31FourTerm
open SignedBall

/-- Integer polynomial certificates for radii zero through four. -/
theorem small_balls (n : Nat) :
    bound n 0 = 1 ∧ bound n 1 = 2*n+1 ∧ bound n 2 = 2*n^2+2*n+1 ∧
    3*bound n 3 = 4*n^3+6*n^2+8*n+3 ∧
    3*bound n 4 = 2*n^4+4*n^3+10*n^2+8*n+3 := by
  induction n with
  | zero => decide
  | succ n ih =>
    obtain ⟨h0,h1,h2,h3,h4⟩ := ih
    simp only [bound.eq_2, show List.range 4 = [0,1,2,3] by decide,
      show List.range 3 = [0,1,2] by decide, show List.range 2 = [0,1] by decide,
      show List.range 1 = [0] by decide, List.range_zero, List.map_cons,
      List.map_nil, List.sum_cons, List.sum_nil, Nat.reduceAdd, Nat.reduceSub,
      h0,h1,h2]
    exact ⟨True.intro, by ring, by ring, by nlinarith, by nlinarith⟩

/-- Every evaluation rule on signed coefficient vectors obeys the same ceiling,
even if the rule has collisions. -/
theorem image_bound {G : Type*} [DecidableEq G] (eval : List Int → G) (n : Nat) :
    3*((vectors n 4).map eval).toFinset.card ≤ 2*n^4+4*n^3+10*n^2+8*n+3 := by
  rw [← (small_balls n).2.2.2.2]
  apply Nat.mul_le_mul_left
  rw [← vectors_length]
  simpa using List.toFinset_card_le ((vectors n 4).map eval)

theorem frozen_ceiling {G : Type*} [DecidableEq G] (eval : List Int → G) :
    ((vectors 195 4).map eval).toFinset.card ≤ 973947521 := by
  have h := image_bound eval 195
  norm_num at h
  omega

theorem insufficient_through_237 {G : Type*} [DecidableEq G]
    (eval : List Int → G) {n : Nat} (hn : n ≤ 237) :
    ((vectors n 4).map eval).toFinset.card < 2147505292 := by
  have h := image_bound eval n
  have boundAt : 2*n^4+4*n^3+10*n^2+8*n+3 ≤
      2*(237:Nat)^4+4*237^3+10*237^2+8*237+3 := by gcongr
  norm_num at boundAt
  omega

end M31FourTerm
