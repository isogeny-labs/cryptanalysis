# Torsion-paired S3 roots and a fused W20 product-span query

**One right S3 quadratic now serves both rational two-torsion preimages of a
public ECC2K-130 point.** On the frozen N131 W20 source, the exact paired
Sage query cut target-dependent quadratic solves from 1,056,360 to 528,180
while retaining all 2,112,720 product proposals and the same four zero-hit
ordinary source rows. A native fused quadratic-algebra gate also checked the
entire 264,090-left-root source against all four preimages under one
600-second/4-GiB cap. The native A/B/A query times were 169.014 s fused,
191.506 s unfused, and 249.715 s fused on this shared host; the spread leaves
the wall-time ordering unresolved.

## Exact paired algebra

Write `s3(u,d,z)=(udz)^2+udz+u^2+d^2+z^2` in the raw `1/x` chart. For
nonzero `d,z` and their inverses `e=1/d`, `f=1/z`, direct multiplication gives

`(dz)^2 s3(u,e,f) = s3(u,d,z)`.

The frozen [four preimages](../n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json)
have raw reciprocal targets satisfying `z0*z1=z2*z3=1`; the input JSON stores
the shifted chart `1/(x+1)`, so the runner verifies its conversion to `1/x`
before any query. The predecessor
[`TorsionCoordinate.lean`](../n131_w20_paired_raw_quotient_20261016/TorsionCoordinate.lean)
connects these inverses to addition by `(0,1)` on `y²+xy=x³+1`. Thus every
nonzero right root `d` for preimage 0 or 2 yields the partner root `1/d` for
preimage 1 or 3. The source product proposals are

`p0=(1+H)d+H/d`, `p1=(1+H)/d+Hd`,

with the same fixed right-pair coefficient `H`. The paired Sage solver solves
only the two representative quadratics, then tests both products against the
same frozen source index. Its sample checks all 512 derived partner root sets
against separate direct quadratic solves; no exceptional zero root occurred
in the sample or full public-target query.

The native gate takes a further step. For a representative quadratic
`A d²+B d+E=0`, both products are affine elements of the *same* quotient
algebra:

`E p0=((1+H)E+HA)d+HB`,

`E p1=((1+H)A+HE)d+(1+H)B`.

It advances both affine states through the existing 19-step linearized
product-span recurrence, sharing `A`, `B`, `E`, the denominator, and the
step coefficient. Counting the C++ recurrence body, a fused step uses 13
field multiplications and 5 squarings for the two predicates, versus 16
multiplications and 6 squarings in two separate invocations. Exact source
recovery and distinct-column checks follow any span hit. The fallback calls
the archived exact root path when `A=0` or `E=0`; neither case occurred in
these four ordinary queries.

## Frozen measurements and controls

The curve is `EC1N131Ckb1heb5f1998f20b`, with the repository's polynomial
field representation `t^131+t^13+t²+t+1`; the public workload ID is
`cc09e7eb202a`. The fixed W20 seed is `898618`, right Frobenius rotation is
18, the source has 132,045 usable pair codes, and each full target query
scans 264,090 left pair roots. Source preparation and target queries are
separate intervals. Every new run used one worker and the 600-second and
4-GiB limits; times are ordinary-host diagnostics. The frozen source and
binary hashes, inputs, cap, and receipts are in the local protocol/result
files.

| Query on the same public point | Quadratic solves | Four-preimage span/source hits | Setup | Target query | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived Sage linear half-trace, four separate preimages | 1,056,360 | 0 source hits | separate | 324.237 s | 304.8 MB |
| Paired Sage, [full result](full_result.json) | 528,180 | 0 source hits | 43.955 s | 149.911 s | 365.0 MB |
| Unfused native four-query comparator, [result](unfused_result.json) | root extraction only on gate hits | 0 span hits | 17.598 s | 191.506 s | 10.0 MB |
| Fused native A, [result](native_result.json) | root extraction only on gate hits | 0 span hits | 15.483 s | 169.014 s | 16.0 MB |
| Fused native A repeat, [result](native_repeat_result.json) | root extraction only on gate hits | 0 span hits | 26.947 s | 249.715 s | 9.8 MB |

The paired Sage and archived four-preimage result have exactly 528,180
proposals per preimage and zero eligible source hits. The native results have
zero span hits, zero exceptional quadratics, and complete scans for each
preimage; [verification.json](verification.json) and
[comparison.json](comparison.json) replay those counts, hashes, caps, and
cross-run identities. The native A/B/A host variation is larger than the
22.492-second first-pair difference, so the field-operation saving has not
established a wall-time improvement. These stage intervals exclude public
preimage construction, source preparation, a complete seven-pair relation
search, relation rank, target descent, scalar replay, and paired rho; the
complete single-target online interval is therefore still open and the
candidate ID remains `null`.

The [constructed partner control](positive_partner_partial.json) was capped
at 40 seconds after scanning 50,432 of 264,090 left roots in its first
target pair. It found the exact distinct-column source hit `(3,16722)` on
the *derived partner* side, with coordinates identical to the archived
[positive result](../n131_w20_quadratic_algebra_20261014/result_positive.json).
Its `CENSORED_TIME` status describes the partial control scan; the hit is a
correctness certificate for the new side of the fused recurrence.

## Checked proof and next gate

[`TorsionS3.lean`](TorsionS3.lean) proves the S3 reciprocal identity and
root equivalence, the inverse-affine substitution, and both fused initial
states. `lean TorsionS3.lean` under `leanprover/lean4:v4.34.1` passed, and
the four `#print axioms` outputs in [lean_output.txt](lean_output.txt) list
only Lean's standard `propext`, `Classical.choice`, and `Quot.sound`. The
[proof map](PROOF_MAP.md) records the exact hypotheses and the remaining
curve-point formalization bridge.

This experiment shares work between two public preimages of **one** partial
sum constraint. The next target-conditioned gate should keep at least two
pair outputs unresolved, represent their source-product membership in a
small quotient algebra, and use the public target to reject a whole code
family before either pair-code list is expanded. An unpinned N41 ordinary
seven-pair control should first measure exact family rejection and useful
relation recovery; only a source-bound implementation fitting the N131
one-worker 600-second/4-GiB envelope advances to this frozen public point.
