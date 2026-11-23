import Mathlib

/-! Two equiprobable hypotheses swap the auxiliary-only and plain-only
probabilities. Each observation records just the paired hit bits. For iid
uniform group points the affinity of the panel is the single-draw affinity
raised to the number of observations. Optimal accuracy is (1+TV)/2.
This model describes sample-only inference with unknown orientation. The
complete public census already determines the orientation directly.

For 15000 independent draws the resulting upper bound is 50.068 percent
correct. The three archived walks give auxiliary minus plain hit differences
of -7, +27 and +24 at the common 5000-trial cutoff. Their walk dependence is
outside the iid model. The complete census advantage of 8834 points predicts
only 0.061704 excess hits in 15000 draws with uniform marginals. -/
namespace M31PairedCoverage

open Finset

/-- Total variation squared is bounded by one minus affinity squared.
The arrays are square roots of the two probability mass functions. -/
theorem tvAffinity {I : Type*} [Fintype I] (a b : I → ℝ)
    (ha : ∀ i, 0 ≤ a i) (hb : ∀ i, 0 ≤ b i)
    (hA : ∑ i, (a i)^2 = 1) (hB : ∑ i, (b i)^2 = 1) :
    ((∑ i, |(a i)^2 - (b i)^2|)/2)^2 ≤ 1 - (∑ i, a i*b i)^2 := by
  have dif (i : I) : |(a i)^2 - (b i)^2| = |a i-b i| *(a i+b i) := by
    rw [sq_sub_sq, abs_mul, abs_of_nonneg (add_nonneg (ha i) (hb i)), mul_comm]
  have hm (i : I) : |a i-b i|^2 = ((a i)^2+(b i)^2)-2*(a i*b i) := by
    rw [sq_abs]; ring
  have hp (i : I) : (a i+b i)^2 = ((a i)^2+(b i)^2)+2*(a i*b i) := by ring
  have h := sum_mul_sq_le_sq_mul_sq univ (fun i => |a i-b i|) (fun i => a i+b i)
  simp only [hm, hp, sum_sub_distrib, sum_add_distrib, ← mul_sum, hA, hB] at h
  simp_rw [dif]
  nlinarith

/-- With equal prior probabilities, any deterministic decision rule is
bounded by (1+TV)/2. A randomized rule averages deterministic accuracies. -/
theorem decisionBound {I : Type*} [Fintype I] (a b : I → ℝ) (rule : I → Bool)
    (hA : ∑ i, a i = 1) (hB : ∑ i, b i = 1) :
    (∑ i, if rule i then a i else b i)/2 ≤ (1+(∑ i, |a i-b i|)/2)/2 := by
  have h : (∑ i, if rule i then a i else b i) ≤
      ∑ i, (a i+b i+|a i-b i|)/2 := by
    apply sum_le_sum
    intro i _
    cases rule i <;> simp only [Bool.false_eq_true, ite_false, ite_true]
    · linarith [neg_le_abs (a i-b i)]
    · linarith [le_abs_self (a i-b i)]
  rw [← sum_div, sum_add_distrib, sum_add_distrib, hA, hB] at h
  linarith

/-- Affinities multiply under an independent product. -/
theorem affinityProduct {I J : Type*} [Fintype I] [Fintype J]
    (a b : I → ℝ) (c d : J → ℝ) :
    (∑ ij : I × J, (a ij.1*c ij.2)*(b ij.1*d ij.2)) =
      (∑ i, a i*b i)*(∑ j, c j*d j) := by
  rw [Fintype.sum_prod_type, sum_mul]
  apply sum_congr rfl
  intro i _
  rw [mul_sum]
  exact sum_congr rfl (fun j _ => by ring)

/-- For the four-outcome table in counts.csv the loss of affinity from one
is (sqrt(A)-sqrt(B))^2/N, with A and B the discordant counts. -/
theorem censusLoss :
    (Real.sqrt 148383130 - Real.sqrt 148374296)^2 / 2147505293 ≤ 613 / 10^13 := by
  have ha := Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 148383130)
  have hb := Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 148374296)
  have ha' : (12180:ℝ) ≤ Real.sqrt 148383130 := (Real.le_sqrt (by norm_num) (by norm_num)).mpr (by norm_num)
  have hb' : (12180:ℝ) ≤ Real.sqrt 148374296 := (Real.le_sqrt (by norm_num) (by norm_num)).mpr (by norm_num)
  have hn := sub_nonneg.mpr (Real.sqrt_le_sqrt (by norm_num : (148374296:ℝ) ≤ 148383130))
  have h := mul_nonneg hn (add_nonneg (sub_nonneg.mpr ha') (sub_nonneg.mpr hb'))
  have hle : Real.sqrt 148383130 - Real.sqrt 148374296 ≤ 8834/24360 := by nlinarith
  have hs := sq_le_sq' (by linarith : -(8834/24360:ℝ) ≤ Real.sqrt 148383130 - Real.sqrt 148374296) hle
  linarith

theorem panelBound (aff tv : ℝ) (h0 : 0 ≤ aff) (h1 : aff ≤ 1)
    (hc : 1-aff ≤ 613/10^13) (ht : tv^2 ≤ 1-aff^30000) :
    (1+tv)/2 < 50068/100000 := by
  have decay (n : ℕ) : 1-aff^n ≤ n*(1-aff) := by
    induction n with
    | zero => simp
    | succ n ih =>
      rw [pow_succ, Nat.cast_succ]
      have := mul_nonneg (sub_nonneg.mpr (pow_le_one₀ (n := n) h0 h1)) (sub_nonneg.mpr h1)
      nlinarith
  have small := decay 30000
  norm_num only [Nat.cast_ofNat] at small
  by_contra! h
  have hh : 0.00136 ≤ tv := by linarith
  nlinarith [mul_self_le_mul_self (by norm_num : (0:ℝ) ≤ 0.00136) hh]

end M31PairedCoverage
