# Proof map

| Result | Lean declaration | Exact hypotheses | Current verification |
| --- | --- | --- | --- |
| Every derived row lies in the source row span | `ClasspartSpanBound.derived_mem_source_span` | Arbitrary field F; finite source/relation indices; finite coordinate type; each derived row is the finite coefficient sum of source rows | Build and axiom audit recorded in `formal/build-output.txt` |
| Derived row span is included in source span | `ClasspartSpanBound.derived_span_le_source_span` | Same | Build and axiom audit recorded in `formal/build-output.txt` |
| Baseline plus derived span is included in baseline plus source span | `ClasspartSpanBound.augmented_span_le` | Same, with arbitrary finite baseline index | Build and axiom audit recorded in `formal/build-output.txt` |
| Augmented rank and rank-gain upper bounds | `ClasspartSpanBound.augmented_rank_le`, `ClasspartSpanBound.rank_gain_le` | Same; dimension over F | Build and axiom audit recorded in `formal/build-output.txt` |
| Ten D79 instances satisfy the coefficient-row hypothesis and measured ranks | `run_sage.py` | Sealed selections, challenges, audits; q as recorded; all 40 source equations and derived rows verified on each curve | Sage replay and receipt checks; no full Lean encoding of curve arithmetic or stored matrices |

The formal theorem uses mathlib's field, finite-dimensional vector-space, submodule-span, and finrank foundations. The exact bridge from integer coefficients and D79 elliptic-curve points to Lean's abstract vectors is checked in Sage and is not a Lean theorem. The general span/rank bound has no assumption about a curve, subgroup, Hecke operator, or support restriction; these enter the instance replay.
