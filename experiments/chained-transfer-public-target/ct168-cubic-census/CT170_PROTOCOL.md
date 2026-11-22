# CT170 prospective canonical-census integrity and clean public-Q timing custody

Date: 2026-11-16. **Standing [pcc:unverified].** This protocol is fixed before the new controls and before the next CI run; it is not a primitive-pricing or complete-solve superiority claim.

## Scope and exact inherited sources
- Reuse merged CT168/169 `census.json`, `generic-crosscheck.json`, `ct168_trace_audit.py`, `ct169_audit_mutation_test.py`, CT167's **corrected** public-`Q` `ct167_sextic_control.py`, and existing workflow. Do **not** rerun the private 695/701 norm fixture or change original raw outputs.
- Frozen CT168 direct census: source `(points=11092788,zero=3,square=5546392,nonsquare=5543172)`; twist `(11086129,0,5543064,5546503)`; deliberately mutated twist `(11086348,3,5543172,5546392)`, all over `q=223^3=11089567`. The independent generic counter must exactly agree componentwise.
- Exact source before follow-up: `ct168_trace_audit.py` Git blob `dced7b96de8df72ba13967675fc24329fe843310`; `ct167_sextic_control.py` Git blob `d8192943e3ab66feee35e02c20a64ebb908d5df7`.

## Predeclared failure and success tests
1. Demonstrate whether the current auditor accepts a coordinated data mutation **without changing the recorded source trace or point count**: set source `zero_rhs_x -= 2`, `nonzero_square_x += 1`, `nonsquare_x += 1`; update corresponding generic `zero -= 2` and `nonzero_square += 1`. This preserves all x/point partition sums and the frozen source group order but changes the already frozen raw component counts. Acceptance is a real contract defect; preserve this prepatch control.
2. Independently test a coordinated mutant control mutation: `mutated_twist.nonzero_square_x += 1`, `nonsquare_x -= 1`, `points += 2`; update independent `n += 2, nonzero_square += 1`. This preserves the x partition but changes the deliberately mutated control's frozen output. No point-count trace assertion currently covers that row.
3. Add fail-closed exact canonical row component comparisons to `ct168_trace_audit.py`, independently of the existing cross-counter and Hasse/trace checks. Add actual mutation tests for both attacks under ordinary and optimized (`python3 -O`) Python. Keep all prior 13 negative controls.
4. Run unchanged, independently structured C++17 x enumerators in existing bounded workflow and compare both unchanged JSON outputs and the immutable `trace-audit.json`. Fail if the new guards reject either legitimate counter.
5. Preserve (instead of silently discarding) the **already specified**, balanced, 16 cold-process *public-Q* CT168 toy timing transcript in source CI: record exact commit SHA, Python/host fingerprint, actual 16-row JSON, SHA-256 digest, same-cohort source and twist totals, RSS, and A/A variation. The child never receives oracle scalar `k`. One hosted CI job is producer-level exploratory evidence, not an approved benchmark, not independent signed PCC and not a calibrated C169/C13/D price.
6. Negative controls must remain explicit: forbidden `--k`, off-curve target, arbitrary row mutation, type/substitution. No new paid workload, native executor, or protected merge.

## Acceptance and limits
- New tests fail on the two *prepatch* semantic mutations and pass after the exact-component guard; canonical CT168 aggregate results remain byte-identical.
- Existing original census tests and public-target 16 cold solves still pass. Record per-run outcomes as success/failure with exact CI link. A source-only passing job never becomes a signed verified execution or a claimed cheaper ECDLP algorithm.
- Pairing is only a four-target order-73 control, on a hosted nondedicated runner. Cold wall time is **not** the same-host native norm-reuse primitive gate and **not** a comparison with best optimized Rust rho/BSGS/index calculus. Distinguish direct source BSGS and transported toy BSGS; never extrapolate to prime31.
- The current owner STOP and unavailable independent full-corpus custody/authenticated object-store and signed PCC gates persist, as tracked by [crypto issue #3904](https://github.com/isogeny-labs/crypto/issues/3904).

Follow-up decision: if the toy transferred arm is slower, retain the negative and return attention to a source-compatible explicit transfer and the approved 695/701 norm-point pricing; if it is faster, treat it only as an exploratory hint until isolation, stronger baselines, all setup and memory, and independent signed verification exist. [pcc:unverified]
