# Unpinned eight-leaf phi relation on an N41 public endpoint

An exact four-plus-four group join found an eight-leaf relation for the frozen
N41 phi endpoint with every leaf code and sign free. Independent Sage replay
checked the raw point sum, its cofactor-4 subgroup projection, and an
eight-column relation row. The public run used one native worker, completed
in 8.182 s parent wall time, and sampled 630,407,168 B combined peak RSS.
The run is an algorithmic relation-search measurement on an ordinary host.

## Instance and method

The field is `GF(2^41)` with polynomial representation `u^41+u^3+1`, and the
curve is `y^2+xy=x^3+1`. The subgroup has order `549756390943`, cofactor 4,
and polynomial-coordinate generator `[455966146946,419221426429]`.
The exact curve ID is `EC1N41Ckb1hecdf2425a2f7` under the candidate-catalog
canonical record in [identity_correction.json](identity_correction.json).
The source protocol gives the endpoint and generator in ONB coordinates; the
exporter checks an explicit field isomorphism and converts them into the
polynomial representation used by the native join. The endpoint was archived
in an earlier N41 control, so this is an exposed-point method check; no leaf
state was supplied to the native public arm. The eight slots are phi
Frobenius positions 0 through 7. Each has 30 valid codes and both signs,
giving 60 free states per slot. The full projected factor base has 2,132
distinct subgroup points before sign/Frobenius folding and 26 columns after
folding.

For slots 0 through 3, the implementation enumerates all four-leaf sums and
indexes them by the exact group point. For slots 4 through 7, it enumerates
four-leaf sums and looks up `target − right_sum`. A hit is accepted only after
the native group equality check; [audit_sage.py](audit_sage.py) independently
reconstructs every selected leaf from the source phi formula and checks the
same equality in Sage. [row_sage.py](row_sage.py) verifies its projected orbit
coefficients and full subgroup row. The frozen inputs and limits are in
[protocol.json](protocol.json); [verify.py](verify.py) checks their hashes,
receipts, and correction record without modifying them.

## Results

| Arm | Native result | Parent wall | Native elapsed at hit | Sampled combined peak RSS | Independent replay |
| --- | --- | ---: | ---: | ---: | --- |
| Positive control | hit; parent status `PRODUCER_FAILURE` after one monitor miss | 31.689 s | 29.750 s | 630,194,176 B | passed |
| Frozen public endpoint | `COMPLETE_HIT`; no monitor misses | 8.182 s | 7.673 s | 630,407,168 B | passed |

The public hit uses state IDs `[12,51,56,38,3,7,54,23]`, leaf codes
`[18,50,56,42,5,10,55,27]`, signs `[0,1,0,0,1,1,0,1]`, and eight distinct
folded columns `[6,3,23,14,22,5,11,18]`. Sage verifies the polynomial
raw sum `[1394337093058,666063635884]` and subgroup projection
`[676316511776,1577965118814]`; [row_result.json](row_result.json)
contains the ONB-coordinate relation terms and coefficients. The native
elapsed interval starts before input loading and table construction; the
parent interval includes launch, monitor, and process exit. These are
relation-query diagnostics. `candidate_id` and a complete single-target
online speedup stay null until the factor-base log system, target recovery,
scalar replay, and paired same-point rho run are measured.

The source phi protocol recorded `curve_id: null`. The first frozen export,
run, audit, and row receipts copied an unrelated N41 curve ID from an earlier
workload. [identity_audit_sage.py](identity_audit_sage.py) independently
mapped the source generator and derived the corrected ID above; the original
files remain byte-for-byte intact and are linked by hashes in
[identity_correction.json](identity_correction.json). Read the original
`curve_id` fields as superseded metadata, while using the corrected identity
for this result.

## Transfer gate for N131

This join is exact and witness preserving, but direct four-leaf storage does
not fit the N131 phi state count. Q1358 has 532 valid phi x lifts per slot;
even choosing just one sign per lift, one four-leaf side has
`532^4 = 80,102,584,576` combinations. An 8-byte
entry would take 640,820,676,608 B, over 149 times the 4-GiB cap. A
32-byte entry would take 2,563,282,706,432 B. The prior Q1358 N131
15-summand ordinary public query reached its 600-second cap with an
indeterminate solver state; the receipt is in the
[Q1358 result](../n131_phi_torsion_frobenius_domains_20261005/diagnostic_runs/public_q_phi_v3_20261013T184000Z/RESULT.md).

The next experiment is a frozen N131 two-leaf partial-sum inventory: enumerate
all `532^2 = 283,024` x-lift pairs for selected slot pairs, with both signs
recorded separately, measure exact distinct group sums and Frobenius/sign
quotient sizes, then test an exact
target-conditioned compatibility filter against an unpinned public endpoint.
Any filter must preserve all hits under independent replay. A 4-GiB/600-s
promotion requires a measured reduction of the four-leaf state frontier,
including preprocessing and false positives, before a new ordinary query.
