# N131 W33 free-code resultant filter

**Removing source-validity witnesses cut the N131 two-pair circuit from
15,225 to 6,841 AND gates while preserving the known positive root.**
Both 32-bit source codes remained free, and the constructed positive's
complete circuit assignment passed all 20,655 clauses and 4,963 native
XOR rows. A one-worker search ended `BOUNDED_UNKNOWN` at both the
120-second pilot cap and the full 600-second cap. This isolates source-code
search, rather than validity-witness size alone, as the next algorithmic
bottleneck for this representation.

The gate preceding this build was a [complete N41 unrestricted-code
census](../n41_w11_allcode_resultant_filter_20261018/RESULT.md): across
25 frozen residuals and 26,214,400 code pairs, its sole resultant zero
was the archived positive, with no invalid-code roots. This is a
control for the filter strategy; N131 roots must still be decoded and
checked against source validity and exact curve addition.

| Item | Exact setting |
| --- | --- |
| Curve | `EC1N131Ckb1heb5f1998f20b`; `GF(2)[u]/(u^131+u^13+u²+u+1)`, `y²+xy=x³+1` |
| Source | W33, seed mask `898618`, 32 free bits per source code, product-basis rank 32 |
| Pair rotations | 0 and 18 Frobenius steps |
| Positive point | `(5517532314023373700997554907490549211, 1154446546775871399813774752133352167830)` |
| Positive source codes | `(3,16722)`, used only for construction and arithmetic replay |
| Public point | `(877610862732227974378969808549299291499, 2063336771837286479337213121437715536874)`; query gated |
| Envelope | One CryptoMiniSat 5.14.7 worker, parent wall 600 s, sampled combined RSS cap 4 GiB |
| Candidate identity | `candidate_id: null`; complete factor base and target pipeline unresolved |

The [builder](build_circuit.py) uses the same frozen 13-term polynomial
as the [exact-validity circuit](../n131_w33_freecode_resultant_20261018/RESULT.md),
including the two-code distinctness clause. It omits trace and inverse
constraints for source-point validity. Therefore a SAT model would be a
candidate code pair that still requires the source and group checks;
the equation itself remains a necessary condition for an exact pair.
The [pure-integer audit](independent_audit_result.json) independently
rebuilt the two positive source products in `GF(2^131)` and evaluated
the exported polynomial to zero.

| Stage | Exact-validity circuit | Filter circuit |
| --- | ---: | ---: |
| AND gates | 15,225 | 6,841 |
| Variables | 21,194 | 11,868 |
| CNF clauses | 46,073 | 20,655 |
| Native XOR rows | 5,643 | 4,963 |
| Formula bytes | 2,947,526 | 1,566,457 |
| Positive free-code SAT | `BOUNDED_UNKNOWN` at 600.067 s | `BOUNDED_UNKNOWN` at 600.098 s |

The filter reduced AND gates by 55.1% and formula bytes by 46.9%.
Its 120-second pilot ended `BOUNDED_UNKNOWN` at 120.082 s with
65,650,688 B sampled combined peak RSS; the full query ended
`BOUNDED_UNKNOWN` at 600.098 s with 131,317,760 B. All queries were
ordinary-host stage diagnostics, not isolated IC/rho comparisons. The
first Python runner attempt exited before solver startup because that
interpreter lacked `psutil`; the exact failure is in
[first_attempt_error.txt](first_attempt_error.txt). Both measured
queries then ran through the checked repository Sage launcher. The
[runtime receipt](sage_runtime_info.json) was saved before the build.

The [verification result](verification_result.json) checks frozen source
hashes, formula hash, assignment result, terminal solver output, caps,
and both receipts. Run `python3 verify.py` here to replay it. The
existing [Lean proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md)
covers the generic elimination implication with its exact hypotheses;
the N131 coefficient export and finite-field replay are computational
checks of this instance. No new structural theorem is asserted here.

The next experiment should eliminate or reject *blocks of first source
codes jointly* under the target-conditioned quartic and the rotated
second product subspace. A valid transfer must keep both source codes
unpinned, recover a constructed positive within the same resource
envelope, and then test the frozen ordinary public point. Further
source-validity clause removal alone has no measured positive-search
benefit under the current 600-second cap.
