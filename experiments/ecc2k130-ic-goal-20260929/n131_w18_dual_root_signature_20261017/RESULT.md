# W18 reciprocal-root signatures: a degree-six obstruction

For the 33,191 valid W18 selectors on `EC1N131Ckb1heb5f1998f20b`, the
reciprocal-root differences have rank **17** in the 131-bit field-coordinate
space. Their annihilator has dimension **114**. Its root-invariant evaluations
have rank **113** as functions on those selectors and distinguish every valid
selector. The remaining annihilator combination is an explicit nonzero
57-bit-weight linear functional that vanishes on all **66,382** recorded
pair roots. The complete output span has rank **130**.

An exact rank intersection rules out every informative linear combination of
these root-invariant signatures with an ANF of degree at most **six** in the
17 selector bits, restricted to the valid codes. The degree-six ANF feature
space has 21,778 independent evaluation columns; its intersection with the
113-dimensional informative signature space has dimension zero. Thus this
specific plan to add cheap low-degree selector-to-output equations needs at
least degree seven. The full signatures still provide exact lookup keys for
the saved source; this experiment measures their algebraic encoding cost.

## Method and exact scope

Let `a0(c), a1(c) ∈ F₂¹³¹` be the two saved standard reciprocal coordinates
for valid source code `c`. Set

`U = span_F₂ {a0(c) + a1(c) : c valid}`.

For `ℓ ∈ U⊥`, linearity gives `ℓ(a0(c)) = ℓ(a1(c))`; the readable proof and
Lean declaration are in the [proof map](PROOF_MAP.md). The first frozen
[`census.py`](census.py) constructed `U⊥` with high-pivot elimination,
evaluated its 114 masks on every source code, and screened individual mask
bits through ANF degree four. The second frozen [`intersect.py`](intersect.py)
computed the intersection of the entire signature space with degree-zero
through degree-five ANF spaces. The independently frozen [`audit.py`](audit.py)
used low-pivot elimination, independently read the table, recomputed all
ranks through degree five, checked both roots against the global vanishing
mask, and found output span rank 130. The third frozen
[`degree6.py`](degree6.py) extended the full intersection to degree six;
[`degree6_low.py`](degree6_low.py) independently matched that result using
low-pivot elimination and a separately constructed annihilator.

| Maximum ANF degree | Feature columns / rank | Signature rank | Intersection rank |
| ---: | ---: | ---: | ---: |
| 0 | 1 / 1 | 113 | 0 |
| 1 | 18 / 18 | 113 | 0 |
| 2 | 154 / 154 | 113 | 0 |
| 3 | 834 / 834 | 113 | 0 |
| 4 | 3,214 / 3,214 | 113 | 0 |
| 5 | 9,402 / 9,402 | 113 | 0 |
| 6 | 21,778 / 21,778 | 113 | 0 |

The output hyperplane mask is
`0x5f90004b7c0f8784ac98a13264581e5b9` (Hamming weight 57). The
low-pivot audit independently verified zero parity of this mask on every
saved `a0` and `a1`. The field representation, source geometry, code law,
and group-addition checks are inherited from the frozen
[`n131_w18_linked_signature_prefix_20261012`](../n131_w18_linked_signature_prefix_20261012/RESULT.md)
table (`rows.tsv.gz`, SHA-256
`0ea58b6963469c754d74294a87e8ca2dcdf7a5d7c8d1672355fc0f2477a6af67`).
Its all-row Sage replay records 33,191 codes, 66,382 roots and 265,528
signed point additions in
[`fast_audit_result.json`](../n131_w18_linked_signature_prefix_20261012/fast_audit_result.json).
This is a finite census for that exact source and code law. The proposed
full IC pipeline remains at `candidate_id: null`.

## Frozen execution and evidence

| Stage | Status | Elapsed | Workers / cap | Evidence |
| --- | --- | ---: | --- | --- |
| Dual census | `PASS_W18_DUAL_ROOT_SIGNATURE_CENSUS` | 3.99 s | 1 / 180 s | [`protocol.json`](protocol.json), [`result.json`](result.json), [`run.stdout`](run.stdout) |
| Full intersection, degrees 0–5 | `PASS_W18_DUAL_ANF_INTERSECTION` | 3.96 s | 1 / 180 s | [`intersection_protocol.json`](intersection_protocol.json), [`intersection_result.json`](intersection_result.json) |
| Independent low-pivot replay | `PASS_INDEPENDENT_LOW_PIVOT_REPLAY` | 5.25 s | 1 / 180 s | [`audit_protocol.json`](audit_protocol.json), [`audit_result.json`](audit_result.json) |
| Degree-six extension | `PASS_DEGREE6_EXTENSION` | 16.36 s | 1 / 180 s | [`degree6_protocol.json`](degree6_protocol.json), [`degree6_result.json`](degree6_result.json) |
| Independent degree-six replay | `PASS_INDEPENDENT_DEGREE6_LOW_PIVOT` | 35.59 s | 1 / 180 s | [`degree6_low_protocol.json`](degree6_low_protocol.json), [`degree6_low_result.json`](degree6_low_result.json) |

The first two frozen census attempts stopped at parser assumptions before
algebra: `root_bit` is a discriminator from 0 through 16, and `code` is a
selector encoding rather than a copy of `mask_a`. Their source, protocols,
raw output, and failure notes remain in [`attempt1`](attempt1/FAILURE.md)
and [`attempt2`](attempt2/FAILURE.md). The corrected parser and every later
protocol were frozen before each run. [`verify.py`](verify.py) checks source
bindings, cross-stage receipts, expected ranks, failure retention, and Lean
output. These are unisolated finite algebra diagnostics; their elapsed times
are task accounting, not an IC-versus-rho wall comparison.

## Next experiment

Derive the analogous output parity, if one exists, from the frozen N41 pair
source and add it as one redundant XOR row per pair to the N41 output-derived
selector circuit. Run an unpinned ordinary N41 target with
the same target, source, solver, one-worker 600-second and 4 GiB limits, and
compare clause propagation, search conflicts, and verified relation outcome
against the unmodified circuit. If the extra row has no measured benefit,
retire this linear-signature branch. If it helps, replay an unpinned N131
ordinary-point query with exact source and resource receipts before assigning
an IC candidate ID or making a single-target speed claim.
