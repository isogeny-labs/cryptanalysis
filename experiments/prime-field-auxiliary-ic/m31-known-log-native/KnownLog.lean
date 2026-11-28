import Mathlib

/-!
The algebraic recovery step for a signed known-log pair. The coefficients
`s` and `t` may be negative, covering both representative signs. If an exact
group relation is checked, subtracting the search offset recovers the target
as a generator multiple. This theorem is independent of the M31 fixture and
does not assert that the Rust pair lookup returns a correct relation or that
one implementation is faster than another.
-/

theorem known_log_two_sum {A : Type*} [AddCommGroup A]
    (G Q : A) (a s t : ℤ)
    (h : Q + a • G = s • G + t • G) :
    Q = (s + t - a) • G := by
  calc
    Q = (s • G + t • G) - a • G := by
      exact eq_sub_iff_add_eq.mpr h
    _ = (s + t - a) • G := by simp [add_zsmul, sub_eq_add_neg]
