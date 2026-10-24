# A three-code quotient rejects 22 complete N41 boxes

One 64-dimensional quotient over `GF(2^41)` represents eight product-code
families at once and tests their three-pair incidence with a public residual.
Across a frozen lexicographic set and an independently hash-selected holdout,
the exact fingerprint rejected **22 of 23 unique complete boxes**. The
remaining box contains the archived ordinary witness triple `(24,37,10)`.
Checked Sage specialized **184 distinct code families** and their **1,472
exact roots**, confirming every box decision. A direct S3 geometry audit
identified the single zero-norm root as first-two chart `801447660706` in
that witness triple.

## Method and frozen inputs

The field is `GF(2)[t]/(t^41+t^3+1)`, curve
`EC1N41Ckb1h7d5e80d3c4d0`, with the W8 seed-56 pair table. The four
suffix pair states are fixed at IDs `(0,14,109,51)`, leaving the first three
pair product codes free. The public residual chart is `112961062585`.
Column disjointness permits **38,874** three-code families, of which **720**
complete 2×2×2 boxes are available at the selected product-code prefix
depth. The first run froze seven lexicographic boxes plus the witness box.
The holdout froze the first 15 SHA-256-ranked boxes outside that set using
the domain tag recorded in `holdout/freeze.py`, and repeated the witness
box as a positive control. All choices preceded their respective symbolic
runs. The exact source hashes and one-worker, 300-second, 4-GiB caps are in
each `protocol.json`. `candidate_id` is `null` for this component experiment.

The eight-dimensional coefficient ring represents the two choices on each
of the three axes. The worker specializes the degree-eight `H` once in this
ring. In the resulting 64-dimensional quotient it builds the third-pair
eliminated norm `Q` and multiplies equality factors for representation bits
`0..23` of `Q`. Zero residue excludes all eight code families of a box.
The construction and formal soundness conditions are in `PROOF_MAP.md`.

| Frozen run | Boxes | Distinct families in run | Rejected at 8 / 12 / 16 / 24 bits | Final result | Producer wall | Producer peak RSS |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| Lexicographic + witness | 8 | 64 | 5 / 6 / 7 / 7 | 7 rejected, witness survives | 52.804 s | 27,459,584 B |
| Hash holdout + witness repeat | 16 | 128 | 10 / 14 / 15 / 15 | 15 rejected, witness survives | 43.720 s | 28,164,096 B |

The first run checked 512 roots and 576 specialized H coefficients in
8.902 s of Sage audit time. The holdout checked 1,024 roots and 1,152
coefficients in 16.832 s. Both audits found one zero of `Q`, in the repeated
witness box. The first run also checked direct S3 against the norm on all
512 roots. The archived seven-state witness sums exactly to raw target
`(1970584690684,115750356512)` and its fourfold to public target
`(1458168294740,1672312028033)`.

The producer's exclusive timing for the first run was 0.039 s setup,
0.331 s symbolic H, 0.119 s eliminated norm, and 52.313 s fingerprint
work. For the holdout it was 0.036 s, 0.408 s, 0.096 s, and 43.178 s.
Loop and serialization time is the rounding remainder. These are
ordinary-host component diagnostics; no one-target online IC/rho timing
or performance tier is attached to them. The current geometry still fixes
four suffix states, and only 184 of the 38,874 eligible families have been
covered by these symbolic runs.

## Next iteration

Free one suffix pair-code axis while retaining a complete quotient-box
certificate and the exact public-target witness. Freeze ordinary N41
positive and negative controls first, then measure the full traversal cost
and target-dependent work under the same one-worker, 4-GiB cap. Promote to
the frozen N131 public point only after that unpinned N41 gate passes.

Reproduce the receipts with `python3 verify.py` in this folder. The checked
Sage launcher and pinned Lean command used for the audits are recorded in
`PROOF_MAP.md` and the two `sage_runtime_info.json` files.
