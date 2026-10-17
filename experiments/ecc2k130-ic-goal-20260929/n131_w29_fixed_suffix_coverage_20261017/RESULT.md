# W29 fixed-suffix completion needs target-conditioned suffix selection

For the aligned N131 W29 source, one fixed three-pair suffix can expose at
most **576,460,750,155,939,840** distinct two-pair completions, even if
every one of the `2^28` canonical codes is valid and every allowed signed
pair sums to a different group point. On the frozen N131 subgroup, this is
at most **8.4704×10⁻²²** of uniform targets. A hypothetical **600 billion**
target-independent suffix probes per advice value still cover at most
**5.0822×10⁻¹⁰** of uniform targets per advice value. At that generous
probe count, the counting bound requires at least **983,826,355 advice
values, or 30 bits**, before it permits 50% coverage. This is a necessary
information threshold for this fixed-proposal model, not a prediction of
algorithmic success.

## Exact source and counting model

The frozen curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[u]/(u^131+u^13+u²+u+1)`, with prime subgroup order
`680564733841876926932320129493409985129`. The [audited W29 source
sample](../n41_n131_aligned_quotient_transfer_20261017/n131_result.json)
has 28 free canonical code bits. A code gives at most four signed pair
states, so two *different* codes give at most 16 signed assignments. With
`N=2^28`, one fixed suffix has at most

`M=16 binom(N,2)=576460750155939840`

two-code completion points. Source-invalid codes, repeated folded columns,
group-sum collisions, and exceptional charts can only decrease this count.
The bound applies to the complete two-pair oracle; it does not depend on
the implementation speed of the [direct S3 inverse](../n41_n131_s3_code_inverse_20261017/RESULT.md).

For each target-advice value, suppose a method fixes at most `k` suffixes
independently of the target *within that advice value*, then tests their
exact two-pair completion sets. If the advice alphabet has `C` values,
the number of successful subgroup targets is at most `C k M`. Thus a
uniform target satisfies

`Pr[success] ≤ min(1, C k M/r)`.

An oriented suffix is one proposal in this count; testing another
Frobenius orientation consumes another proposal unless its group images
are already included in the completion-set bound.

The hypothetical `k=600,000,000,000` grants one billion complete suffix
probes per second for 600 seconds. It is an arithmetic ceiling for the
model, not a measured worker rate. The [count result](result.json) gives
unrounded rational numerators and denominators; the [protocol](protocol.json)
pins the source records and code before the calculation.

| Exact N131 quantity | Value |
| --- | ---: |
| Canonical code upper bound | 268,435,456 |
| Signed states per slot upper bound | 1,073,741,824 |
| Two-code completions per fixed suffix, at most | 576,460,750,155,939,840 |
| Fixed suffixes needed before 50% coverage is permitted with one advice value | 590,295,812,557,728,915,461 |
| Coverage bound for 600 billion suffixes and one advice value | `345876450093563904000000000000 / 680564733841876926932320129493409985129` |
| Advice values needed before 50% is permitted at 600 billion suffixes per value | 983,826,355 |
| Minimum binary advice width for that many values | 30 bits |

The bound handles target-dependent advice only through its declared
alphabet. A selector that uses more than 30 bits of the public point, or
adapts its suffixes using richer target-dependent computations, must be
measured and analyzed on its own terms. The fixed-suffix S3 inverse can
serve as its completion oracle, but improving that oracle alone does not
meet this W29 relation-search gate.

## N41 control and interpretation

The aligned N41 W9 source has 71 valid canonical codes and four signed
states per code, giving at most `16 binom(71,2)=39,760` completions for
one fixed suffix. The [previous 65-query panel](../n41_n131_s3_code_inverse_20261017/result.json)
retains its independently checked ordinary relation at the archived
suffix and finds zero point-family hits among 64 frozen miss suffixes.
The positive suffix was selected from an existing relation, so it is a
correctness control. The miss-panel acceptance filter inspected whether
the target residual had a usable coordinate, so the uniform-target bound
for 64 *target-independent* suffixes (`2544640/549756390943`) is a
separate reference calculation, not an empirical success estimate for
that filtered panel.

The [Lean proof map](PROOF_MAP.md) checks the two-level advice and suffix
counting implication and both large-integer N131 certificates. The
[terminal verifier](terminal.json) rechecks all source bindings, exact
integer results, and Lean axiom output. The calculation uses no Sage job
or CPU timing claim. This is a decomposition-stage bound with
`candidate_id: null`.

## Next experiment

Keep at least two suffix code families unresolved when the public point
first enters the algebraic constraint. A concrete next gate is a
source-aware resultant or quotient-ring predicate on a first-pair code
family and a **two-family suffix block**. Freeze the full N41 code-box
domain before evaluation, preserve the orientation-6 ordinary witness,
and measure how many whole boxes are rejected before signed-state
expansion. Carry all construction and failed-query costs into a source-bound
N131 work and 4-GiB memory projection. The first N131 public-relation run
follows only if that projection fits one worker and 600 seconds.
