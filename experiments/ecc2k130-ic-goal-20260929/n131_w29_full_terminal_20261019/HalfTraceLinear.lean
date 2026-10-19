import Std
import Init.Grind.Ring.Basic

namespace HalfTraceLinear
open Lean.Grind

/-- The normalized S3 quadratic's Artin–Schreier argument is a square.
The variables `u` and `v` are the inverses of the nonzero coordinates
`c` and `t`; the executable field inverse is audited separately. -/
theorem normalized_s3_argument_square {F : Type} [Field F]
    (c t u v : F) (hcu : c * u = 1) (htv : t * v = 1)
    (hchar : ∀ x : F, x + x = 0) :
    (1 + (c * t)^2) * (c + t)^2 * (u * v)^2 =
      (c + u + t + v)^2 := by
  have htwo : (1 : F) + 1 = 0 := hchar 1
  grind

private theorem square_add {F : Type} [Field F]
    (x y : F) (hchar : ∀ z : F, z + z = 0) :
    (x + y)^2 = x^2 + y^2 := by
  have htwo : (1 : F) + 1 = 0 := hchar 1
  grind

private theorem fourth_add {F : Type} [Field F]
    (x y : F) (hchar : ∀ z : F, z + z = 0) :
    (x + y)^4 = x^4 + y^4 := by
  have htwo : (1 : F) + 1 = 0 := hchar 1
  grind

/-- The 66-term half-trace is represented by `halfTraceRec 66`: each
successive term raises the input to its fourth power. -/
def halfTraceRec {F : Type} [Field F] : Nat → F → F
  | 0, _ => 0
  | n + 1, x => x + halfTraceRec n (x^4)

theorem halfTraceRec_add {F : Type} [Field F]
    (n : Nat) (hchar : ∀ z : F, z + z = 0) (x y : F) :
    halfTraceRec n (x + y) = halfTraceRec n x + halfTraceRec n y := by
  induction n generalizing x y with
  | zero => simp [halfTraceRec]; grind
  | succ n ih =>
      simp only [halfTraceRec, fourth_add x y hchar, ih]
      grind

/-- Rational-coordinate trace conditions on two reciprocal coordinates
force the target-conditioned Artin–Schreier argument to have zero trace. -/
theorem s3_trace_compatible {F : Type} [Field F]
    (Tr : F → F) (hadd : ∀ x y, Tr (x + y) = Tr x + Tr y)
    (hsquare : ∀ x, Tr (x^2) = Tr x)
    (c t u v : F) (hc : Tr (c + u) = 0)
    (ht : Tr (t + v) = 0) :
    Tr ((c + u + t + v)^2) = 0 := by
  have hz : Tr (c + u + t + v) = 0 := by
    grind
  grind

/-- A linear half-trace map may be evaluated by XORing its images of the
set input bits. This is the mathematical contract of the 131-column table. -/
theorem linear_table_fold {F : Type} [AddCommMonoid F]
    (H : F → F) (hzero : H 0 = 0)
    (hadd : ∀ x y, H (x + y) = H x + H y)
    (xs : List F) : H (xs.foldr (· + ·) 0) =
      (xs.map H).foldr (· + ·) 0 := by
  induction xs with
  | nil => simp [hzero]
  | cons x rest ih =>
      simp [hadd, ih]

#print axioms HalfTraceLinear.normalized_s3_argument_square
#print axioms HalfTraceLinear.halfTraceRec_add
#print axioms HalfTraceLinear.s3_trace_compatible
#print axioms HalfTraceLinear.linear_table_fold

end HalfTraceLinear
