import Std
import Init.Grind.Ring.Basic

namespace FunctionSelector
open Lean.Grind

/-- Scaling the first nonzero coefficient places a field-valued function
    in its unique projective normalization chart. -/
theorem normalized_chart {K : Type} [Field K]
    (coeff : Fin 7 → K) (j : Fin 7)
    (hj : coeff j ≠ 0)
    (hfirst : ∀ i : Fin 7, i < j → coeff i = 0) :
    (coeff j)⁻¹ * coeff j = 1 ∧
      ∀ i : Fin 7, i < j → (coeff j)⁻¹ * coeff i = 0 := by
  constructor
  · exact Field.inv_mul_cancel hj
  · intro i hi
    rw [hfirst i hi]
    grind

/-- A finite linear evaluation, used for one Riemann--Roch row. -/
def dot {K : Type} [Field K] : List (K × K) → K
  | [] => 0
  | (a, b) :: xs => a * b + dot xs

/-- Scaling all function coefficients scales every point-row evaluation. -/
theorem dot_scale {K : Type} [Field K] (scalar : K)
    (xs : List (K × K)) :
    dot (xs.map (fun pair => (scalar * pair.1, pair.2))) =
      scalar * dot xs := by
  induction xs with
  | nil => grind [dot]
  | cons p xs ih =>
      simp only [List.map_cons, dot]
      rw [ih]
      grind

/-- A vanishing point-row equation survives projective normalization. -/
theorem scaled_zero {K : Type} [Field K] (scalar : K)
    (xs : List (K × K)) (hzero : dot xs = 0) :
    dot (xs.map (fun pair => (scalar * pair.1, pair.2))) = 0 := by
  rw [dot_scale, hzero]
  grind

/-- Every nonzero seven-coefficient vector has a first nonzero coordinate. -/
theorem first_nonzero {K : Type} [Field K] (coeff : Fin 7 → K)
    (hnonzero : ∃ i : Fin 7, coeff i ≠ 0) :
    ∃ j : Fin 7, coeff j ≠ 0 ∧
      ∀ i : Fin 7, i < j → coeff i = 0 := by
  classical
  by_cases h0 : coeff (0 : Fin 7) = 0
  ·
    by_cases h1 : coeff (1 : Fin 7) = 0
    ·
      by_cases h2 : coeff (2 : Fin 7) = 0
      ·
        by_cases h3 : coeff (3 : Fin 7) = 0
        ·
          by_cases h4 : coeff (4 : Fin 7) = 0
          ·
            by_cases h5 : coeff (5 : Fin 7) = 0
            ·
              by_cases h6 : coeff (6 : Fin 7) = 0
              ·
                rcases hnonzero with ⟨i, hi⟩
                have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) ∨ i = (2 : Fin 7) ∨ i = (3 : Fin 7) ∨ i = (4 : Fin 7) ∨ i = (5 : Fin 7) ∨ i = (6 : Fin 7) := by omega
                rcases hidx with e0 | e1 | e2 | e3 | e4 | e5 | e6
                all_goals simp_all
              ·
                refine ⟨6, ?_, ?_⟩
                · simpa using h6
                · intro i hi
                  have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) ∨ i = (2 : Fin 7) ∨ i = (3 : Fin 7) ∨ i = (4 : Fin 7) ∨ i = (5 : Fin 7) := by omega
                  rcases hidx with e0 | e1 | e2 | e3 | e4 | e5
                  all_goals simp_all
            ·
              refine ⟨5, ?_, ?_⟩
              · simpa using h5
              · intro i hi
                have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) ∨ i = (2 : Fin 7) ∨ i = (3 : Fin 7) ∨ i = (4 : Fin 7) := by omega
                rcases hidx with e0 | e1 | e2 | e3 | e4
                all_goals simp_all
          ·
            refine ⟨4, ?_, ?_⟩
            · simpa using h4
            · intro i hi
              have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) ∨ i = (2 : Fin 7) ∨ i = (3 : Fin 7) := by omega
              rcases hidx with e0 | e1 | e2 | e3
              all_goals simp_all
        ·
          refine ⟨3, ?_, ?_⟩
          · simpa using h3
          · intro i hi
            have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) ∨ i = (2 : Fin 7) := by omega
            rcases hidx with e0 | e1 | e2
            all_goals simp_all
      ·
        refine ⟨2, ?_, ?_⟩
        · simpa using h2
        · intro i hi
          have hidx : i = (0 : Fin 7) ∨ i = (1 : Fin 7) := by omega
          rcases hidx with e0 | e1
          all_goals simp_all
    ·
      refine ⟨1, ?_, ?_⟩
      · simpa using h1
      · intro i hi
        have hidx : i = (0 : Fin 7) := by omega
        rcases hidx with e0
        all_goals simp_all
  ·
    refine ⟨0, ?_, ?_⟩
    · simpa using h0
    · intro i hi
      omega

/-- Forward, propagation, and exclusion clauses make two selected states
    at distinct positions inconsistent. The finite implementation omits
    forward clauses at the last position, which is never the earlier one. -/
theorem sequential_amo_sound (selected pref : Nat → Prop)
    (forward : ∀ i, selected i → pref i)
    (step : ∀ i, pref i → pref (i + 1))
    (exclude : ∀ i, selected (i + 1) → ¬ pref i)
    (i j : Nat) (hij : i < j) (hi : selected i) (hj : selected j) : False := by
  have propagate : ∀ k, pref i → pref (i + k) := by
    intro k
    induction k with
    | zero => simp
    | succ k ih =>
        intro h
        simpa only [Nat.add_succ] using step (i + k) (ih h)
  have hprev : i + (j - i - 1) = j - 1 := by omega
  have hnext : (j - 1) + 1 = j := by omega
  have hp : pref (j - 1) := by
    rw [← hprev]
    exact propagate (j - i - 1) (forward i hi)
  rw [← hnext] at hj
  exact exclude (j - 1) hj hp

#print axioms first_nonzero
#print axioms normalized_chart
#print axioms dot_scale
#print axioms scaled_zero
#print axioms sequential_amo_sound
end FunctionSelector
