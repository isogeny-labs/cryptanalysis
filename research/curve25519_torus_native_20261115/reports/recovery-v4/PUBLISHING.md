# Companion report storage handoff

The PDF was rendered and inspected locally. This repository's artifact policy
selects it for storage, and this repository has no artifact upload workflow.
The shared `s3://setec-astronomy-artifacts/store` upload is staged through the
maintained trusted uploader in [crypto PR #4364](https://github.com/isogeny-labs/crypto/pull/4364):

`research/curve25519_torus_native_20261115/reports/consumer-recovery-v4-upload/`

Expected original PDF: 121028 bytes,
SHA-256 `b17b53b7d259465ea7963670e6367474bbeec33cfd99ba6e8e066242cb2c8317`.
The staging `ORIGIN.json` binds the byte-identical payload to consumer commit
e6bd7641ed6fea1e8b2c6c2b442b1574f0ced3b0. It deliberately records pre-upload
state. Do not infer upload success from that file.

Completed on 2026-11-16: the trusted artifact-autofix commit
[`f8a7dbc5f7f2d82c3c2f9209d3dd7a1d025a9fb8`](https://github.com/isogeny-labs/crypto/commit/f8a7dbc5f7f2d82c3c2f9209d3dd7a1d025a9fb8)
contains the exact expected digest/byte count. The maintained `write_manifest`
and `write_gitignore` helpers register that same shared-store object here as
`report.pdf`. Only its tracked copy is removed, keeping the inspected local
bytes. Local artifact verification reports one hydrated entry and no problems.
`STORE_RECEIPT.json` records the source manifest and immutable commit. No new
upload, policy exception, credential export, object deletion or scientific
claim is involved.

Hydrate and verify before opening:

```sh
python3 tools/artifacts/artifacts.py pull research/curve25519_torus_native_20261115/reports/recovery-v4
python3 tools/artifacts/artifacts.py verify research/curve25519_torus_native_20261115/reports/recovery-v4
```

This publishing step does not change the report, controls or open solver and
geometric obligations. Required PR checks must pass on the current head.

The check-in also found unchanged base blockers: PCC-20261115-8d2645 uses
plain-text test logs as recompute/JSON reports, and the base ledger is already
72227 bytes, above the consumer's 64-KiB data threshold. This change preserves
that ledger and its prefix; no policy or unrelated claim is modified to bypass
the gate. These baseline issues are reported on PR #1591 for upstream repair.
