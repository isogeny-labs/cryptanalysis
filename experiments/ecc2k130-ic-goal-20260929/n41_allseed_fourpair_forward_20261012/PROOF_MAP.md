# Proof map: N41 all-seed four-pair forward roots

The executed field is `GF(2)[t]/(t^41+t^3+1)` and the curve is
`y²+xy=x³+1`, with subgroup order `549756390943` and cofactor four.
The Boolean circuit uses eight source reciprocals, four Frobenius rotations,
and seven forward S3 root links on the nonzero reciprocal chart.

| Result | Declaration or check | Status and exact hypotheses |
| --- | --- | --- |
| Replacing seven forward roots by S3 links preserves the source witness and terminal constraint | `N41FourPairForward.forward_relation_sound` in [ForwardRoot.lean](ForwardRoot.lean) | `lean ForwardRoot.lean` passed with `leanprover/lean4:v4.34.1`; `#print axioms` reports no axioms. The result assumes `rootSound` for every link and parameterizes the topology. |
| Reciprocal root formula for `p=ab`, `A=1+p²`, `C=(a+b)²`: `Az²+pz+C=0` | Written proof in [prior proof map](../n41_w8_tenpair_functional_20261012/PROOF_MAP.md); seven concrete links in [Sage audit](audit_result.json) | Faithful Lean proof of the degree-41 field arithmetic, half-trace, inversion circuit, exceptional branch and S3 equivalence remains open. Formalization is partial at this bridge. |
| Eight distinct folded source columns sum to the frozen raw preimage and project to the public point | [Sage audit](audit_result.json) | Checked against the frozen source geometry and seven branch bits. The receipt is one constructed positive control, not a natural-yield sample. |
| Boolean formula accepts its constructed primary assignment | [build result](build_result.json) | Every 361,813 CNF clause and 97,546 native XOR row was checked. A Lean semantics of the circuit emitter remains open. |

The structural theorem is source and target preserving but does not replace
the concrete arithmetic or gate-semantics obligations. The host lacks
`lean4checker`; `lean` output is retained in [lean_check.txt](lean_check.txt).
