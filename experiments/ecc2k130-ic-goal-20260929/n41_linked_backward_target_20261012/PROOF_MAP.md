# Proof and verification map

| Result | Formal or executable evidence | Exact scope |
| --- | --- | --- |
| Backward terminal equality is equivalent to the forward group sum | `backward_target_equiv` in [BackwardTarget.lean](BackwardTarget.lean), checked by [lean_check.txt](lean_check.txt) | Arbitrary type with explicitly assumed associative addition, right identity, and left/right inverse laws. No curve-specific assumption is hidden. |
| Each encoded affine link uses a nonzero denominator and computes the stated point | [v4 runner](v4/run.py), [control model](v4/control.stdout), [verifier](verify.py) | Concrete `GF(2^41)` nonexceptional chart. Curve-law soundness is checked by executable arithmetic, not imported into Lean. |
| The linked positive witness satisfies all source, relation, and target equations | [v4 control result](v4/control.json), [earlier independent Sage audit](../n41_n131_linked_frobenius_pair_20261012/audit_result.json), [verifier](verify.py) | The ten selected source points, nine distinct source edges, nine additions, and raw target preimage 3. |
| The public query is censored at its 180-second cap | [v4 public result](v4/public.json), [raw solver stream](v4/public.stdout), [verifier](verify.py) | No terminal SAT/UNSAT line for this frozen query and resource cap. |
| Formula bytes and producer failures are retained | [archive receipt](archive_result.json), [v1](failure.json), [v2](v2/failure.json), [v3](v3/failure.json), [verifier](verify.py) | Four attempted XCNFs are byte-replayable; v1 stopped before writing a formula. |

The formalization is complete for the group rearrangement theorem and partial for the full concrete circuit: it does not define the binary elliptic-curve group law or prove that the CNF/XOR serialization implements each affine addition. Those bridges are separately checked on the positive model and remain open as Lean obligations. Exceptional backward additions are outside the encoded chart and require their own branches for source completeness.
