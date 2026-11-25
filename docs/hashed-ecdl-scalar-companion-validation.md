# Scalar tensor companion import checks — 2026-10-29

Current-main correction: a separate native tensor crate and its own
[validation receipt](hashed-ecdl-tensor-validation.md) landed during this work.
That receipt is preserved at its existing path; this renamed document records
the earlier independent Python import. Earlier missing-native statements below
refer to the initial checkout. The companion is not the native crate's backend.

Prime-field follow-up: the reference now includes the officially named Certicom
ECCp-131 instance, modular coordinate constraints and shared relation/certificate
plumbing. The combined development suite passes 39 tests. See the separate
[prime validation receipt](../experiments/hashed-ecdl-tensor-reference/prime-development/README.md)
for commands, exact published parameters, graph checks and the unresolved
challenge solve. The original 28-test import receipt below is preserved.

This is a repository-import and development-correctness receipt, not a
performance experiment or an IC/rho comparison.

- Destination: `isogeny-labs/cryptanalysis`, with a paired documentation update
  in `isogeny-labs/crypto`.
- Cryptanalysis base: `9bd6f84bbf8742da38cbd9147ef48bb2d6abb387`.
- Crypto base: `d0ddf51582cadec6e9b39a4b0f4a376e5dab8535`.
- The existing Rust implementation and its API declarations are unchanged.
- Local Python unit check: 28 passed, zero failed, including the OpenSSL
  comparisons, recursive contractions and coordinate witness checks.
- The original source snapshots and compact result records are retained in
  the study with their original, narrower interpretation. No new experiment
  or admitted speed measurement was run during this import.

Reproduction:

```sh
cd experiments/hashed-ecdl-tensor-reference
python -m unittest -v test_ecc2k test_tensor_contraction test_tensor_encoding
```

The complete current import-check output is retained separately as
`import-unit-tests.txt` in the study. Historical `results/test-results.txt`
is not overwritten.

## Import-time validation and setup gaps

- The default-policy challenge attempt remains a budget-exhausted exact leaf;
  it is not a recovered relation or scalar and not a mathematical obstruction.
- The prime-field composition missing at import is now implemented in the
  companion described above. A native implementation is separately available
  on main; independent parity/audit, companion general ell>1, formal
  verification and the asymptotic proof remain open.
- `cargo test --release --lib` was attempted in crypto and exited 127 because
  Cargo is not installed in this execution environment. No Rust tests or
  full-library pass are claimed for this documentation-only companion update.
- Conductor is absent (127). The documented warn-and-allow setup fallback in
  `crypto:docs/CONDUCTOR.md` applies; no shared reservation is claimed.
- Two sparse-checkout setup commands used an unsupported option or the wrong
  working directory. They were corrected from the repository root. These
  setup errors did not change source, tests or frozen outputs.
- An initial PR was opened against the wrong personal paper fork. It was
  closed without merging. The user then identified these two Isogeny Labs
  repositories; the corrected changes are scoped here.

Hosted CI, review and merge status belong to the corresponding PRs and are
not asserted by this local receipt.
