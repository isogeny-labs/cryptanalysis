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

Pending: read the subsequent trusted artifact-autofix commit and its
`.artifacts.json`, require the exact digest and byte count, then use the
maintained `write_manifest` / `write_gitignore` helpers to register that
same shared-store object here as `report.pdf`. Remove only its tracked copy
with `git rm --cached`, keeping the local inspected bytes. Commit the pointer
and receipt provenance to PR #1591. No new upload, policy exception, credential
export, object deletion or scientific claim is needed.

Once the pointer exists, hydrate and verify before opening:

```sh
python3 tools/artifacts/artifacts.py pull research/curve25519_torus_native_20261115/reports/recovery-v4
python3 tools/artifacts/artifacts.py verify research/curve25519_torus_native_20261115/reports/recovery-v4
```

This publishing step does not change the report, controls or open solver and
geometric obligations. Required PR checks must pass on the current head.
