#set page(paper: "a4", margin: 1.2cm)
#set text(font: "Liberation Sans", size: 9pt)
#set heading(numbering: "1.")

= P-192/P-224 curve-audit certificates: independent replay

*27 October 2026 UTC · T-499 · producer `dc73f979` · checker `b0f44d3`*

This packet validates concrete archived certificate arithmetic in an independent Python exact-integer implementation. It does not claim a complete Lean proof, authenticated archived Rust/Sage execution, a fresh Sage point count, or general curve safety.

#figure(image("certificate-boundary.svg", width: 100%), caption: [Green is freshly replayed arithmetic; blue is pinned historical material; orange marks the remaining execution and formal bridge.])

== Evidence matrix

#table(
  columns: (1.75fr, 1fr, 1fr, 2.15fr), inset: 4pt,
  [*Check*], [*P-192*], [*P-224*], [*Interpretation*],
  [Recursive prime certificates], [9 nodes], [8 nodes], [Complete factorizations and Lucas witnesses for `p` and `r`; 41 / 40 small prime factors checked by exact division.],
  [Curve / generator arithmetic], [pass], [pass], [Nonsingular; affine point on curve; separate scalar multiplication gives `[r]G=O`.],
  [Candidate order], [pass], [pass], [`r|N`, squared Hasse candidate bound and strict spacing hold.],
  [Archived fields], [match], [match], [Source and input digests, order, trace, twist and statuses are consistent; execution is not authenticated.],
  [Negative controls], [5 rejected], [5 rejected], [Wrong input hash, witness, factor exponent, point and candidate order were rejected.],
)

== Execution and limits

The plan and 12-input SHA-256 inventory were committed before execution as `906c7c6`. The initial checker `95a1cce` failed at module load because the host has Python 3.9; that failure is retained. The corrected checker `b0f44d3` ran as `python3 -I replay.py` and exited zero. Its bytes matched the committed version. `execution-receipt.json` binds command, hashes, result and logs. The complete calculations and control reasons are in `result.json`.

The checker uses exact integers, its own Lucas verifier and affine group arithmetic. Hasse, Lagrange and Lucas are mathematical dependencies, not Lean formalizations of this concrete curve. The candidate values agree with archived Rust and Sage fields. Sage's documented `cardinality()` returns the number of rational points, but no Sage runtime was available on this host. Fresh native Rust build/test was deferred because other owned Lean and optimized Rust builds were active; it is *not executed* here. Archive consistency alone does not prove the producer binary correct or authenticate its old run.

The source README correctly labels the Lean theorem as a partial proof. PR #1197 validates only the conditional interval-uniqueness lemma. Prime-field, elliptic group, exact-order, Lagrange, Hasse and natural-interval bridges remain open. No performance numbers were measured, so no metric graph or dashboard was changed.

Full source links, the NIST historical parameter reference, Sage API link, raw outputs and next verification steps are in `report.md` beside this PDF.
