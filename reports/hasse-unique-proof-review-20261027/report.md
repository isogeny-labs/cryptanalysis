# Hasse interval theorem: independent proof review

Review date: 2026-10-27 UTC. Coordination task: T-493. Producer commit:
`dc73f9791dc7d2c61e0c77572d2c3aaeedb30436`. This is a technical review;
it changes no research decision, curve-audit criterion, measured result, or
historical receipt.

## Bound claim and verdict

The exact theorem is `CurveAudit.unique_multiple_in_short_interval` in
`bindings/rust/curve-audit/formal/HasseUnique.lean` (SHA-256
`0e0b14f032203329328910ac0bc0f03db88f508087c4fdb236fd1bbe6d7e49f7`).
For natural numbers, two multiples of `r` within `width` of each other are
equal when `width < r`. Its premises are satisfiable. The source README's
narrow statement is faithful to this declaration.

| Claim | Machine | Fidelity | Overall |
| --- | --- | --- | --- |
| Conditional uniqueness of nearby multiples of `r` | passed on Lean 4.34.1, standard axioms only | faithful_scoped | **validated_scoped** |
| Full formal P-192/P-224 curve order, trace, twist, or implementation correctness | not_verified by this theorem | partial; missing bridges below | **inconclusive** as a formal claim |

The validated claim is arithmetic. It supplies no independent fact that a
curve's actual cardinality or the proposed `N` is a multiple of `r`, or that
both satisfy the needed interval premises. The producer README already calls
the formal proof partial. The checked-in Rust/Sage certificate route and its
archived results are separate computational evidence; this review checked
their source and digest consistency, not fresh end-to-end execution.

## Machine evidence and controls

The coordinator copied exactly the producer-commit theorem, toolchain pin, and
`tools/lean/AuditAxioms.lean` into an isolated tree. Input hashes before and
after the native run were identical; see [machine-receipt.json](machine-receipt.json).
`lean -o HasseUnique.olean HasseUnique.lean` exited 0 and printed the named
declaration's axioms `[propext, Quot.sound]`. The transitive auditor found one
theorem, zero failures, zero trusted `native_decide` exceptions; see
[build.stdout](build.stdout) and [audit.stdout](audit.stdout). This relies on
the installed pinned Lean kernel. `lean4checker --fresh` was unavailable, so
there is no independent binary recheck.

The controls were run in the same isolated tree with Lean 4.34.1. A
`False := by sorry` theorem compiled but the auditor exited 1 with `sorryAx`.
An unknown module exited 1 rather than silently auditing zero theorems.
Lean compiled both an actual adjacent-multiples counterexample at `width=r=7`
and a nonvacuous positive case at `r=7,width=3,n=m=14`. Inputs, exits, digests
and complete logs are in [control-receipt.json](control-receipt.json),
[FalseControl.lean.txt](FalseControl.lean.txt), and
[BoundaryControl.lean.txt](BoundaryControl.lean.txt). The fixture bytes ran as
`FalseControl.lean` and `BoundaryControl.lean` in the isolated scratch tree;
the archived `.txt` suffix keeps intentional test inputs outside the tracked
research theorem source inventory. The counterexample shows why the
strict bound is load bearing; it is not a failure of the stated theorem.

## Independent review and concrete claim boundary

[Reviewer A](hasse-blind-review-A-20261027.md) derived the implication from
the mathematical statement alone, identified the sharp strict bound, and
attested no source, plan, or sibling-report access. [Reviewer B](hasse-source-review-B-20261027.md)
compared the exact theorem with README and the Rust certificate path, checked
the committed P-192/P-224 parameter and receipt digests, and attested no A
access. A had only the blind brief; B had the producer source and precommitted
plan. Their independent conclusions agree on the narrow statement. The
reviewer assignments and prior are in [review-plan.md](review-plan.md),
committed as `3b704f1` before either reviewer reported. Attestations are
self-reported; filesystem reads were not independently monitored. The
autoresearcher independence checker expects a different task-record schema
and was not used as a certificate for this report-only review.

B's integer recomputation found the committed candidate bounds, spacing,
trace and twist arithmetic consistent with the archived fields and historical
P-192/P-224 parameters in [NIST FIPS 186-4 Appendix D.1.2](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.186-4.pdf).
That withdrawn document is used only as a historical parameter source.
Source inspection and hash agreement do not authenticate archived execution
or prove this Rust implementation correct.

## Unresolved formal and validation obligations

1. Bind the concrete JSON parameters and certificates to Lean declarations.
2. Prove the Pratt/Lucas primality checker and its parser sound for the bound inputs.
3. Connect finite-field and point arithmetic code to a nonsingular elliptic group.
4. Establish typed generator membership, nonidentity, exact order `r`, and Lagrange divisibility of the actual group cardinality.
5. Prove Hasse's bound for that curve and convert both squared bounds into a natural interval with width strictly below `r`.
6. Instantiate the arithmetic theorem with the actual cardinality and proposed `N`.
7. Formalize trace and twist identities if those are claimed as Lean results; independently replay the executable certificate path before upgrading its runtime evidence.

The [scope diagram](proof-boundary.svg) shows the proved implication and the
unproved inputs. There are no experimental measurements in this review, so a
performance graph would have no data to plot. This theorem review adds no data
to canonical performance graphs and warrants no graph update. The companion
[PDF](report.pdf) is rendered from `report.typ` with the
diagram embedded and inspected after generation.
