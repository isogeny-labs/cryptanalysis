# D39 rank closure is reproduced by a Hecke-free doubling control

2026-10-30. **Verified finite diagnostic; no IC speedup established.**

The frozen six-arm audit completed after checkpoint upload access was supplied.
The saved Hecke+Atkin–Lehner rank rises from 52 to 63 on the same 64 columns
modulo 11 when either projected equalities or doubling relations are added.
All 64 normalized base logs were recovered and checked in each of four arms.
The follow-up control reaches the same rank 63 using doubling rows alone,
with **zero Hecke rows**. A separate short-Weierstrass implementation verifies
all 256 scalar labels from those four solutions.

## Exact scope and receipts

Curve: X_0(11)=11a1, y^2+y=x^3-x^2-10x-20 over F367; full group order
385=5*7*11, subgroup order 11, projection P -> [35]P. The original 64-point
CM class has D_K=-39 and conductor 6. Its projected points cover all 11
subgroup elements; this is a dense toy configuration.

The unchanged [protocol](PROTOCOL.md) was published in
[PR #1306](https://github.com/isogeny-labs/cryptanalysis/pull/1306) before execution.
The [first receipt](runs/20261030T030848Z/receipt.json),
[launch record](runs/20261030T030848Z/launch.json), stdout/stderr and successful
checkpoint receipt retain the actual attempt. Exit status was 0 under the
60-second cap. Source input SHA-256 is
`4bcc8eb1905a9ed79a47cc31820e722dc7a6ff87f18bb37aeebafa35e6cc6df9`;
the executed checker hash is in the receipt. The launch records the Python
runtime, platform and code revision. Elapsed time is diagnostic only.

| Arm | Total rows | Rank mod 11 | Nullity | Replayed normalized base logs |
| --- | ---: | ---: | ---: | ---: |
| Hecke | 48 | 40 | 24 | not attempted |
| Hecke + Atkin–Lehner baseline | 112 | 52 | 12 | not attempted |
| Baseline + projected equalities/zeros | 166 | 63 | 1 | 64/64 |
| Baseline + doubling | 508 | 63 | 1 | 64/64 |
| Baseline + doubling/tripling | 880 | 63 | 1 | 64/64 |
| Baseline + all additions | 934 | 63 | 1 | 64/64 |

Dense elimination agrees with the frozen independent sparse checker in every
arm. All raw points and full-group Hecke identities pass; all projected
Hecke/Atkin–Lehner and added relations pass group checks. The small-field
point count independently confirms order 385. The audit reports 448 group-add
calls for combined doubling/tripling collection and 10,134 including setup
and verification; these are implementation counters, not a fair end-to-end
comparison or a calibrated cost model.

## Hecke-free control and independent replay

The [control protocol](CONTROL_PROTOCOL.md) was fixed locally after the first
result and is first published with its outcome. It is an exploratory control,
not an independently verifiable holdout. Its
[receipt](runs/20261030-controls/receipt.json) and
[launch](runs/20261030-controls/launch.json) retain exit 0 and hashes.

| Control, with no Hecke or Atkin–Lehner rows | Rows | Rank mod 11 | Nullity |
| --- | ---: | ---: | ---: |
| Projected equalities/zeros only | 54 | 54 | 10 |
| Doubling only | 396 | 63 | 1 |
| Doubling + tripling only | 768 | 63 | 1 |

The independent replay uses X=x-1/3, Y=y+1/2, giving
Y^2=X^3+112X+55 over F367, a separate short-model addition formula and
repeated addition instead of the producer's generalized-model double-and-add.
It checks each projected coordinate, all new control rows and the 256 prior
scalar labels. Anchor column 0 defines the reference generator; no unknown
external-target log or target-descent algorithm is supplied.

Interpretation: the new rows close the finite relation gap, but the same
closure is available without Hecke information. Accordingly this is not
an improvement over the Hecke-free closure baseline and not a pipeline speedup.
The tiny subgroup permits many projected collisions; the result does not
establish comparable relation yield at cryptographic sizes.

## Status and next discriminator

| Requirement | Status |
| --- | --- |
| Required checkpoint before and after execution | verified complete |
| Frozen six-arm diagnostic | verified complete |
| Independent rank checks and anchored replay | verified complete |
| Hecke-free control and independent coordinate/group replay | verified complete |
| Arbitrary-target descent, scalable advantage and matched rho comparison | unresolved |

The previous [blocked report](REPORT.md) and its PDF are preserved as historical
evidence. The [access problem](../../problems/hecke-d39-scalar-closure-execution.md)
is resolved for this session. The remaining
[sparse-closure and descent problem](../../problems/hecke-d39-sparse-closure-and-descent.md)
states the next acceptance criteria: larger pinned classes with sparse,
predominantly distinct projections, matched generic scalar-closure controls,
and verified target descent. No larger-class run was launched in this change.

The new [diagram](result.svg), [rank chart](ranks.svg) and [PDF](result.pdf)
are generated from editable sources. Rebuild with `python3 build_result.py`.
The original D39 schematic and canonical surface-transfer graphs were reviewed
again. This adds a relation-stage result, not a new isogeny edge; those existing
graphs remain unchanged. Original inputs and all earlier evidence are preserved.
