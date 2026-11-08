# Pre-review plan: GLV cap no-worse Lean addition

Frozen before independent reviewer dispatch. Producer branch starts from
cryptanalysis `7a0eeee735bbd80e857d36d7069e388786231014`; the reviewed
input will be its pushed PR head, recorded in the reviewer handoff.

## Claim and prior

The producer claims that `NoWorseLogic.lean` proves exact order facts about
the decimals in `results.json`: the registered pooled-size reject predicate
does not fire on the four published intervals, while the separately reported
`j = 0` upper endpoint exceeds one. The producer also claims a counterexample
to a general implication from pooled passage to a family upper bound, even
for well-formed intervals. The claim does **not** assert family harm,
bootstrap validity, raw-row correctness or execution. [pcc:unverified]

Prior before reviewer reports: high confidence in the integer comparisons;
moderate confidence in source-to-Lean fidelity because the frozen Python
predicate and JSON decimals still need independent inspection; no confidence
added to the original measurement beyond its existing evidence.

## Joints, owners, and worked attacks

| Joint | Owner | Worked attack to try |
| --- | --- | --- |
| Blind order logic and interval well-formedness | Blind algebra reviewer | Derive a counterexample from the rule and endpoints alone. Try an invalid interval and a family upper endpoint below one; check whether the conclusion would still be claimed. |
| Source and value fidelity | Source-fidelity reviewer | Compare the theorem definitions with the actual `analyze.py` no-worse branch and full-precision JSON values. Mutate one lower endpoint, the `>` predicate, and the theorem conclusion; check that the binding/gate refuses each. |
| Lean kernel and transitive axioms | Coordinator | Build exact named source under pinned Lean and `proof-gate.sh`; reject wrong theorem names, holes, custom axioms, native evaluation or omitted modules. |
| Empirical bridge | Coordinator | Check that no reviewer treats the decision-rule proof as proof of bootstrap coverage, source binary identity, or historical solver correctness. |

The blind algebra reviewer receives only a minimal input card with the
predicate and endpoint decimals, without the producer proof or source code.
The source-fidelity reviewer receives the pushed head, source and report but
not the blind review. Reviewers must not read each other's reports before
filing their own attestation. The coordinator composes their findings only
after both reports are frozen.

Known-false controls: a pooled lower endpoint greater than one must make the
predicate fail; a `j = 0` upper endpoint below one must remove the archived
upper-bound counterexample; changed analysis source or changed Lean constants
must fail binding; changed theorem text must fail its PCC declaration pin.

Acceptance is separate for machine status, semantic fidelity and review
outcome. A local build or a signed theorem verdict without independent
source-fidelity review does not complete this review. [pcc:unverified]
