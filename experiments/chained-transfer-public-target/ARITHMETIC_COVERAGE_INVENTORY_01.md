# Arithmetic coverage inventory before priced comparisons

Static source audit at39b932dd/originalproducer3d49af7f,2026-11-14.
This inventory identifies implementation boundaries;it supplies no new
measured totals. Source hashes are in evidence/norm-sampling-prospective-01/sources-checked.json.
[pcc:unverified]

| Boundary | Actual implementation | Coverage obligation |
| --- | --- | --- |
| Native prime/cubic | native/original/common.rs Fp/Kf;powmod;inv_mod_u64;original IC scalar helpers | Real Fp operations and scalar modulus must be distinguished;old bump_* also receives Picard aggregates. [pcc:unverified] |
| Cover prime/cubic | original crypto/src/cryptanalysis/diem_quartic.rs Fq and Kf | Constructor,polynomial and map work occurs outside IC phase accounting. [pcc:unverified] |
| Canonical Picard | original crypto/src/cryptanalysis/plane_quartic_pic.rs private Fq primitives and counter/reset/setup_cost | Count each actual primitive once;old pc bridges may aggregate these again. Resetting object counters must not reset an independent complete ledger. [pcc:unverified] |
| Runtime extension | original isogeny_algos/src/fpr.rs Field implementation,fold,frobenius,inv | API calls alone omit actual nonzero coefficient products,reduction folds,inverse scaling and nested Frobenius work. [pcc:unverified] |
| Extension setup | FpR::from_modulus/new,original Field/Zp and poly Rabin paths,fpm::inv_u64 | Include irreducibility and Frobenius-table construction;prepared reuse is a distinct online scope. [pcc:unverified] |
| End-to-end boundaries | CheckedInstance,old/new Adapter/Norm,degree13/models,admission,solver,independent answer checking | Cold includes all stages;online explicitly retains preparation and amortization assumptions. Hashing,conversion,allocation,memory and raw integer work are not free. [pcc:unverified] |

Implementation should use an isolated versioned source mirror with exact
original snapshots and literal tap diff. Do not modify any original engine,
verifier or current754-input replay subject. Require original arithmetic
outputs and solver records to match,primitive positive controls,reset and
nesting controls,and a source audit of reachable arithmetic before calling
the vector complete. Price operations only after matched calibration and
all original admission/reference requirements. [pcc:unverified]

The norm-assisted sampler protocol is an immediate same-output correctness
candidate. Its high-level call vector cannot discharge this inventory.
