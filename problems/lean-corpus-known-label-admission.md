# Known-label proposed algebra source blocks the current Lean corpus gate

- **Status:** investigating
- **Kind:** implementation gap; native proof evidence missing
- **Affected work:** [corpus gate](../tools/lean/README.md),
  [known-label proposal](../docs/known-label-next-leads-20261028/README.md)
- **Next action owner:** validation continuation, Conductor T-764
- **Last updated:** 2026-10-28

## Problem

The newly merged `docs/known-label-next-leads-20261028/Algebra.lean` has no
native Lean receipt and is outside the existing corpus admission rules.
Consequently the current-main corpus gate fails before compiling additions.
This blocks a passing gate; it is not evidence that a theorem is false.

## Evidence and uncertainty

- **Observed:** PR #1282 merged as
  `47865467f9cc28c316a12ddab017017047815f19`. Native corpus
  [run 40727716430, job 122955370580](https://github.com/isogeny-labs/cryptanalysis/actions/runs/40727716430/job/122955370580)
  failed with `ValueError: unreviewed Lean corpus addition:
  docs/known-label-next-leads-20261028/Algebra.lean` at 16:42:52 UTC.
  Toolchain setup, fixture controls, and the pinned Mathlib cache succeeded.
- **Source:** SHA-256
  `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.
  The producer's `CHECKS.json` explicitly says `unbuilt; no checked proof
  claimed`. Its six Python symbolic/abstract-group checks are separate evidence.
- **Proposed repair:** admit only that path and hash, bind all three shared
  workspace input files, compile with Lean 4.35.0-rc4 / Mathlib
  `021c46bdd042f67b538b9f9871d556a93713a9a9`, require all four qualified
  declaration printouts, and audit the module's non-internal theorems with
  the existing native auditor. No unknown neighboring source is admitted.
- **Local validation:** `python3 tools/lean/test_current_corpus_gate.py -v`
  passed 18 tests (six existing quartic controls and twelve new known-label
  controls). They cover changed source and project bytes, symlinks, exact
  path dispatch, isolated output, wrong namespaces, missing printouts,
  forbidden axioms, empty/failing/wrong-name module audits, compiler failure,
  and source mutation during audit. Runtime outputs in these unit tests are
  mocks, not proof receipts. `git diff --check` passed.
- **Resource limit:** the existing T-650 workload owns
  `migration:memory-heavy-build`; no competing full Lean build was started.
  The existing hosted corpus workflow will perform native validation on the
  proposed head. No new cloud capacity or quota is requested.
- **Not established:** native validity of these four identities until that
  run succeeds, semantic correspondence of graph labels to elliptic groups,
  the proposal's probability claims, or any historical timing/performance claim.

## What would unblock it

- [ ] Successful exact-head corpus run compiling the unchanged proposed
  source with the recorded pins, all four named printouts, and a successful
  native module theorem audit using only standard Lean foundations.
- [ ] All applicable current-head CI passes and a verified guarded merge.

These conditions resolve this admission/build gap. They do not complete
independent mathematical claim-fidelity review or the full cross-repository
historical experiment validation task. The proof map and hypotheses are in
the [gate README](../tools/lean/README.md#known-label-proposed-algebra-source).

## Next discriminating step

Publish the five-file gate repair, then inspect the exact-head hosted check
at the repository's normal check-in cadence. A compiler or axiom-audit failure
requires its actual diagnostic and a scoped fix; an infrastructure failure
remains inconclusive. Do not bypass the gate or replace a native build with
unit-test output. Existing budgets and the exclusive local-build rule remain.

## Resolution and history

Unresolved. This change preserves the original `Algebra.lean`, `CHECKS.json`,
and proposal report. The affected `diagram.svg` and `REPORT.pdf` were checked
for scope: this is a CI admission repair, with no changed graph data,
empirical count, or scientific conclusion requiring a new rendering.

### Independent verifier review follow-up

The prospective review in PR #1285 binds the original producer
`ffeacb44b6a151aebc84619f30a70591eb44e0f6`. Reviewer
`TASK-20261028-298dc6` found two bounded workflow defects: each of the three
workspace inputs could change during a simulated native command without a
post-check, and both CI event path filters omitted `lake-manifest.json`.
These are false acceptance/routing controls, not a demonstrated false Lean
theorem. The original producer version and review will remain archived.

The revised producer rechecks all three project hashes after the native
commands, adds lockfiles to both workflow filters, and includes six changed
input/phase controls (three files, compilation or audit). These controls must
reject the old producer and pass on the revised producer. The affected J3
review and exact-head native CI must be repeated on the new source version;
the first review is not silently applied to changed verifier bytes.
Pre/post hashes cannot detect a transient mutation restored between checks;
native CI runs in its isolated checkout, and installed dependency binaries
retain the stated Lean/Lake trust boundary.
