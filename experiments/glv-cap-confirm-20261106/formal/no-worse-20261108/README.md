# GLV cap no-worse decision-rule proof

This versioned addition formalizes the logical boundary stated in the
[2026-11-08 erratum](../../ERRATUM.md). It does not modify the frozen protocol,
raw experiment, analysis, result JSON, or graph. The source snapshot is
cryptanalysis `7a0eeee735bbd80e857d36d7069e388786231014`; the toolchain is
the repository's `leanprover/lean4:v4.34.1`.
The theorem claim is `PCC-20261108-5903ae`; its standing remains unverified
until a trusted CI verdict is signed on `main`. [pcc:unverified]

## Source and statement binding

`check_binding.py` pins `analyze.py` at SHA-256
`d176871072c0ccd109357aa8369b63e0811573a36bb8dc64f69627f3997b4a22`
and `results.json` at SHA-256
`f196d804397b7a44b3392c11c5b6c99e4154ae70c11fb687f6e376b999911550`.
It checks that the source rejects a pooled-size interval exactly when its lower
endpoint is greater than one, and marks the no-worse check passed when none
is rejected. It loads the JSON decimals without binary-float rounding and
compares all four pooled interval endpoints, the `j = 0` interval, and its
point estimate with the values encoded in `NoWorseLogic.lean` at scale
10^16 and with the blind review card in `BLIND_INPUT.json`. The required
`gate` job runs this binding check on every PR.

| Lean declaration | Exact scope |
| --- | --- |
| `published_pooled_noWorsePass` | The four published pooled-size lower endpoints are at most one; the frozen rule passes on these endpoints. |
| `published_pooled_wellFormed` | All four published pooled intervals have lower endpoint at most upper endpoint. |
| `published_j0_straddles_one` | The separately published `j = 0` 95% interval has lower endpoint below one and upper endpoint above one. |
| `published_j0_point_above_one` | The published `j = 0` point estimate exceeds one. |
| `published_j0_wellFormed` | The published `j = 0` interval has lower endpoint at most upper endpoint. |
| `published_j0_not_bounded_by_pooled_pass` | The published pooled-size intervals pass while the separately published `j = 0` upper endpoint exceeds one. |
| `pooled_pass_does_not_bound_family_upper` | Even for well-formed intervals, passing a predicate that reads only pooled-size intervals does not imply an upper bound on a separate family interval; the published values witness the failure. |

The proof encodes the exact decimal strings printed in `results.json` as
natural numbers scaled by 10^16. Integer order comparisons preserve their
order against one. The readable argument is that the four pooled lower
endpoints are all below one, so the source's reject predicate never fires.
The `j = 0` upper endpoint and point estimate are both above one. Since the
pass predicate does not inspect the family interval, it cannot establish a
family-level no-harm or non-inferiority conclusion. [pcc:unverified]

## Reproduce and limits

From the repository root:

```sh
python3 experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/check_binding.py
lean experiments/glv-cap-confirm-20261106/formal/no-worse-20261108/NoWorseLogic.lean
```

Local Lean 4.34.1 returned exit 0; `#print axioms` reported no axioms for
each of the seven named declarations. `lean4checker --fresh` was unavailable
on this host. Hosted Lean and source-binding gates remain authoritative for
the PR head. [pcc:unverified]
The repository's `tools/lean/proof-gate.sh` also returned `PASS` on this
seven-theorem version: ten declarations audited (seven named theorems and
three structure-generated ones), zero failing and zero trusted native
evaluations. Its local logs are under
`/var/tmp/glv-cap-no-worse-proof-gate-final-20261108`. [pcc:unverified]
The binding check also passed under `python3 -O`; changing a Lean endpoint or
the source reject comparison in a scratch copy made it exit nonzero. [pcc:unverified]

This is an interval-order and decision-rule proof. It does not validate the
bootstrap procedure, coverage probabilities, raw operation counts, actual
family harm, historical binary identity, or solver correctness. The existing
erratum claim `PCC-20261108-6081a3` remains unverified; this addition does
not promote its PCC standing. The missing raw archives and independent
measurement replay remain separate obligations. [pcc:unverified]
