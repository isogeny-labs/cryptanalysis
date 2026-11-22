# An implicit span norm preserves the N41 witness; the general resultant hits its cap

**The frozen three-product constraint admits an exact source-family norm, and
its leading coefficient is a unit on all 39 allowed second codes in the
witness first-code region.** A rank-three symbolic resultant agreed
coefficient for coefficient with an independent native product over eight
span elements. The full rank-seven native residue retained precisely the
archived witness second code 37 and rejected every allowed second code on
the control chart. The direct general-purpose symbolic resultant did not
finish within its 180-second parent cap at rank seven, so this implementation
does not advance to the N131 source-bound gate.

## Exact family condition

The source is the frozen N41 three-product tensor over
`GF(2)[t]/(t^41+t³+1)` for `EC1N41Ckb1h7d5e80d3c4d0`. Fix first product
code `p=24`, a public residual chart `t`, and let `H_{p,t}(q,r)` be the
degree-16-in-`q`, degree-24-in-`r` polynomial obtained by specializing the
[symbolic tensor](../n41_target_chart_symbolic_tensor_20261014/RESULT.md).
For the allowed second-code values, set

`G_p(q)=∏_{j allowed}(q+q_j)`, with `deg G_p=39`.

Let `V` be the third-product binary span. Its monic linearized annihilator
`L_V(r)=∏_{v∈V}(r+v)` has degree `2^rank(V)`. Because it splits into these
distinct field roots, the standard resultant identity gives

`Res_r(H_{p,t}(q,r), L_V(r)) = ∏_{v∈V} H_{p,t}(q,v)`.

Reducing this polynomial modulo `G_p` preserves its value at every allowed
second code. A unit residue excludes the entire first-code region; a
nonunit residue identifies second codes for exact source-labelled fallback.
The positive source triple `(24,37,10)` is retained in the rank-seven
witness panel. This is a target-conditioned *component* on the earlier
witness/control residual panels; it is not an unpinned N41 seven-pair search.

## Bounded experiment

The [protocols](smoke_protocol.json) pin the tensor, code table, source-root
input, checked Sage launcher/runtime, one worker, 180-second parent cap, and
4-GiB RSS threshold. The first smoke and full implementations passed
`H.resultant(L_V)` directly to Sage. A diagnostic retry wrote phase markers
before the cap. The reduced rank-three retry used the monic degree-eight
`L_V` to reduce `H` first. All failed and censored attempts retain their
separate receipts and logs.

| Trial | Span rank / size | Result | Target-dependent norm time | Receipt |
| --- | ---: | --- | ---: | --- |
| Direct Sage resultant smoke | 3 / 8 | `PARENT_TIME_CAP` at 180 s | unknown | [receipt](smoke_receipt.json) |
| Instrumented direct Sage smoke | 3 / 8 | `PARENT_TIME_CAP` at 90 s, after `H` and `G` setup | unknown | [receipt](diagnostic_receipt.json) |
| Reduced Sage resultant | 3 / 8 | exact residue, no accepted second code | 26.529 s resultant; 0.943 s explicit eight-root product | [result](reduced_result.json) |
| Direct Sage resultant full | 7 / 128 | `PARENT_TIME_CAP` at 180 s | unknown | [receipt](full_receipt.json) |
| Native explicit residue oracle, witness | 3 / 8 and 7 / 128 | exact rank-three residue; rank-seven survivor `[37]` | 0.000584 s and 0.214041 s | [result](oracle_result.json) |
| Native explicit residue oracle, control | 3 / 8 and 7 / 128 | no accepted second code | 0.000306 s and 0.016367 s | same result |

The reduced rank-three resultant had `deg_q=128`; after reduction modulo
`G_p`, its 39 coefficient values exactly matched the independent native
residue. [verification_v2.json](verification_v2.json) checks that equality, the
positive/control hit sets, source hashes, cap statuses, and receipts.
Times are ordinary-host component diagnostics. The native and Sage paths use
different arithmetic implementations; the large gap is a falsifier for
this **Sage symbolic-resultant implementation**, not a lower bound on an
implicit norm algorithm.

The leading coefficient of `H` in `r` has degree 16 in `q` and is nonzero
at every one of the 39 allowed second-code values on both charts. The
[native unit check](unit_native_result.json) therefore establishes that it
is invertible in the squarefree quotient
`R=GF(2^41)[q]/(G_p(q))`. A separate Sage polynomial-GCD unit check reached
its 60-second cap and is retained in [its receipt](unit_receipt.json); the
native check evaluates the exact frozen coefficients at every root of `G_p`
and replays both rank-three and rank-seven residues.

## Proof boundary and next implementation

The readable proof of the norm identity is the monic split-resultant
formula above, followed by evaluation modulo the product of distinct
linear factors. The inherited checked Lean theorem
[`JointNorm.product_zero_iff`](../n41_joint_fourpair_resultant_20261012/JointNorm.lean)
formalizes the finite product's exact zero criterion under explicit
no-zero-divisors assumptions. The [proof map](PROOF_MAP.md) identifies the
remaining formal bridge from Sage's resultant and the concrete tensor to
that criterion.

The unit result opens a more specific next gate: work directly in `R`, make
the degree-24 polynomial `H` monic, reduce the sparse `L_V` modulo `H` by
Frobenius squaring, then compute its norm by a **source-labelled quotient
tower or a determinant with exact CRT splitting at nonunit pivots**. That
implementation must be compared with the 39-code explicit oracle, retain
second code 37, and measure complete target-dependent cost before a full
40-first-code N41 panel. An N131 W20 trial would then need a source-bound
projection within one worker, 600 seconds, and 4 GiB; even 600 seconds over
132,045 first codes allows only about 4.54 ms per first-code region before
other online phases. The candidate ID remains `null`.
