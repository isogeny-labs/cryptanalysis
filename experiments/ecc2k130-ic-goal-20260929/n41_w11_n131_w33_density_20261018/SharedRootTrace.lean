import Std
import Init.Grind.Ring.Basic

namespace SharedRootTrace
open Lean.Grind

/-- The reciprocal S3 constraint is a quadratic in its output coordinate.
This coefficient identity is the direct-resolution bridge used by the
fixed-output target filter. -/
theorem s3_output_quadratic
    {F : Type} [Field F] (a b z : F) :
    (a * b * z) * (a * b * z) + a * b * z +
      (a + b) * (a + b) + z * z =
    ((a * b) * (a * b) + 1) * (z * z) +
      (a * b) * z + (a + b) * (a + b) := by
  grind +ring

/-- The trace-shifted half-trace can be applied coefficientwise to a
Boolean-linear field expression. -/
theorem shifted_halftrace_add
    {F : Type} [Field F] (trace halftrace : F → F)
    (trace_add : ∀ x y, trace (x + y) = trace x + trace y)
    (halftrace_add : ∀ x y, halftrace (x + y) = halftrace x + halftrace y)
    (x y : F) :
    halftrace ((x + y) + trace (x + y)) =
      halftrace (x + trace x) + halftrace (y + trace y) := by
  rw [trace_add]
  have hreorder : (x + y) + (trace x + trace y) =
      (x + trace x) + (y + trace y) := by grind +ring
  rw [hreorder, halftrace_add]

/-- In an odd-degree binary field, the trace bit shifts every input into
the trace-zero subspace. The required trace properties are explicit. -/
theorem shifted_trace_zero
    {F : Type} [Field F] (charTwo : ∀ x : F, x + x = 0)
    (trace : F → F)
    (trace_add : ∀ x y, trace (x + y) = trace x + trace y)
    (trace_zero : trace 0 = 0) (trace_one : trace 1 = 1)
    (trace_bit : ∀ y, trace y = 0 ∨ trace y = 1)
    (y : F) : trace (y + trace y) = 0 := by
  rcases trace_bit y with hzero | hone
  · rw [trace_add, hzero, trace_zero]
    grind +ring
  · rw [trace_add, hone, trace_one]
    exact charTwo 1

/-- The shifted half-trace is an Artin-Schreier section on every input;
on trace-zero inputs it gives a root of the original equation. -/
theorem shifted_halftrace_section
    {F : Type} [Field F] (charTwo : ∀ x : F, x + x = 0)
    (trace halftrace : F → F)
    (trace_add : ∀ x y, trace (x + y) = trace x + trace y)
    (trace_zero : trace 0 = 0) (trace_one : trace 1 = 1)
    (trace_bit : ∀ y, trace y = 0 ∨ trace y = 1)
    (halftrace_root : ∀ z, trace z = 0 →
      halftrace z * halftrace z + halftrace z = z)
    (y : F) :
    halftrace (y + trace y) * halftrace (y + trace y) +
      halftrace (y + trace y) = y + trace y := by
  exact halftrace_root _
    (shifted_trace_zero charTwo trace trace_add trace_zero trace_one trace_bit y)

theorem shifted_halftrace_trace_zero
    {F : Type} [Field F] (trace halftrace : F → F)
    (halftrace_root : ∀ z, trace z = 0 →
      halftrace z * halftrace z + halftrace z = z)
    (y : F) (hy : trace y = 0) :
    halftrace (y + trace y) * halftrace (y + trace y) +
      halftrace (y + trace y) = y := by
  have h := halftrace_root y hy
  grind +ring

#print axioms SharedRootTrace.s3_output_quadratic
#print axioms SharedRootTrace.shifted_halftrace_add
#print axioms SharedRootTrace.shifted_trace_zero
#print axioms SharedRootTrace.shifted_halftrace_section
#print axioms SharedRootTrace.shifted_halftrace_trace_zero

end SharedRootTrace
