# Four second-pair products from first-pair curve states

An implicit target-conditioned two-pair membership operator now derives
the four candidate second products directly from the four signed
first-pair curve states. It uses
`q=C₂/x(T-P)+H₂*x(T-P)` for each state `P`. Across every first code in
the frozen N41 control and all 75 valid first codes in the N131 panel,
the four values were distinct, zeroed the exact quartic resultant, and
matched its complete field-root set. The source-span hits and misses
matched independent quartic extraction, including the replayed N131
positive pair `(3,16722)` and the frozen public panel.

The direct formula is a checked [Lean theorem](PROOF_MAP.md) under the
pair-quadratic and reciprocal-coordinate hypotheses. An independent
binary-field [audit](audit.py) re-evaluates every derived product against
the frozen resultant; the checked Sage producer verifies actual curve
points, source traces, four branch states and target subtraction.

## Cost on frozen panels

The first-pair state setup depends on the source construction and can
be reused across target points. The derivation and span-decoding rows
below are target-dependent, exclusive measured phases. Polynomial
evaluation and cross-run replay are correctness checks reported
separately.

| Field | First codes × targets | Reusable state setup | Target derivation | Span decoding | Polynomial checks | Full monitored wall | Peak sampled RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| N41 | 281 × 2 | 8.781 s | 0.317 s | 0.206 s | 5.885 s | 24.128 s | 289,980,416 B |
| N131 | 75 × 2 | 44.650 s | 0.263 s | 0.595 s | 10.846 s | 67.130 s | 244,137,984 B |

The corresponding field-root extraction alone took 29.118 seconds
on the N41 panel and 208.913 seconds on the N131 panel. The direct
target phases totaled 0.524 and 0.858 seconds respectively after
state setup. These are stage measurements on one ordinary host, not
a complete target-decomposition or IC-versus-rho result. In particular,
the public N131 panel had no second-source hit; a higher-arity join or
joint point-decomposition solver is still required for an ordinary
relation. `candidate_id: null` remains the correct pipeline status.

The method replaces quartic factorization after a first source is
chosen. It still visits each chosen first source for every residual
target. The 75-code N131 panel therefore demonstrates a fast exact
membership kernel but leaves the full source search and five-pair
coupling as the next algorithmic gate. The N41 native five-pair join
already supplies an ordinary relation control; its explicit right-pair
index exceeds the N131 4 GiB envelope, so the next experiment must
share this implicit membership work across many residuals or eliminate
first-source families algebraically.

Run `python3 audit.py` in this directory to check all pinned sources,
the N41 promotion gate, 712 four-root identities, exact source hits,
resource receipts and the Lean proof log. Both checked-Sage runs used
one worker, a 600-second parent wall cap and a 4 GiB RSS cap.
