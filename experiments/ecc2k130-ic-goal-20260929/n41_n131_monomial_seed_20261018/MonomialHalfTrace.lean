import Std
import Init.Grind.Ring.Basic

namespace MonomialHalfTrace
open Lean.Grind

/-- Finite prefix of the characteristic-two half-trace polynomial. -/
def halfTraceN {R : Type} [CommRing R] : Nat → R → R
  | 0, _ => 0
  | n + 1, x => x + halfTraceN n (x ^ 4)

/-- The same prefix, expressed as consecutive Frobenius pairs. -/
def pairedTraceN {R : Type} [CommRing R] : Nat → R → R
  | 0, _ => 0
  | n + 1, x => x + x ^ 2 + pairedTraceN n (x ^ 4)

/-- For every characteristic-two commutative ring, applying the half-trace
    prefix to a seed `h²+h` equals the paired Frobenius trace prefix of `h`. -/
theorem halfTraceN_monomial_seed {R : Type} [CommRing R]
    (n : Nat) (h : R) (charTwo : (2 : R) = 0) :
    halfTraceN n (h ^ 2 + h) = pairedTraceN n h := by
  induction n generalizing h with
  | zero => rfl
  | succ n ih =>
      have h4 : (h ^ 2 + h) ^ 4 = (h ^ 4) ^ 2 + h ^ 4 := by
        grind
      have hn := ih (h ^ 4)
      grind [halfTraceN, pairedTraceN]

/-- The first `m` ordinary Frobenius trace terms. -/
def traceN {R : Type} [CommRing R] : Nat → R → R
  | 0, _ => 0
  | m + 1, x => x + traceN m (x ^ 2)

/-- Repeated squaring, kept explicit to state finite-field closure. -/
def frobN {R : Type} [CommRing R] : Nat → R → R
  | 0, x => x
  | m + 1, x => frobN m (x ^ 2)

theorem traceN_two_steps {R : Type} [CommRing R] (m : Nat) (x : R) :
    traceN (m + 2) x = x + x ^ 2 + traceN m (x ^ 4) := by
  have hp : (x ^ 2) ^ 2 = x ^ 4 := by grind
  simp only [traceN, hp]
  grind

theorem pairedTraceN_eq_traceN {R : Type} [CommRing R]
    (n : Nat) (x : R) : pairedTraceN n x = traceN (2 * n) x := by
  induction n generalizing x with
  | zero => rfl
  | succ n ih =>
      rw [pairedTraceN, ih (x ^ 4)]
      rw [Nat.mul_succ]
      exact (traceN_two_steps (2 * n) x).symm

theorem traceN_succ_last {R : Type} [CommRing R]
    (m : Nat) (x : R) :
    traceN (m + 1) x = traceN m x + frobN m x := by
  induction m generalizing x with
  | zero => grind [traceN, frobN]
  | succ m ih =>
      rw [traceN, ih (x ^ 2)]
      simp only [traceN, frobN]
      grind

/-- Full odd-degree finite-field form: zero trace and Frobenius closure
    force `h` to be the half-trace root of the monomial seed. -/
theorem monomial_seed_of_trace_zero {R : Type} [CommRing R]
    (n : Nat) (h : R) (charTwo : (2 : R) = 0)
    (traceZero : traceN (2 * n + 1) h = 0)
    (frobClosed : frobN (2 * n + 1) h = h) :
    halfTraceN (n + 1) (h ^ 2 + h) = h := by
  rw [halfTraceN_monomial_seed (n + 1) h charTwo,
      pairedTraceN_eq_traceN]
  have hs := traceN_succ_last (2 * n + 1) h
  have hn : 2 * (n + 1) = (2 * n + 1) + 1 := by omega
  rw [hn, hs, traceZero, frobClosed]
  grind

#print axioms traceN_two_steps
#print axioms pairedTraceN_eq_traceN
#print axioms traceN_succ_last
#print axioms monomial_seed_of_trace_zero

/-- The odd-degree trace expression, with the closing Frobenius term
    identified with `h`, selects the canonical half-trace root. -/
theorem monomial_seed_halfTrace_root {R : Type} [CommRing R]
    (n : Nat) (h : R) (charTwo : (2 : R) = 0)
    (traceZero : h + pairedTraceN (n + 1) h = 0) :
    halfTraceN (n + 1) (h ^ 2 + h) = h := by
  rw [halfTraceN_monomial_seed (n + 1) h charTwo]
  grind

#print axioms halfTraceN_monomial_seed
#print axioms monomial_seed_halfTrace_root
end MonomialHalfTrace
