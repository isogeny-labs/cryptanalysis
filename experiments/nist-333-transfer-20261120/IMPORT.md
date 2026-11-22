# Import provenance

Imported on 2026-11-20 from the standalone `nist-333` working directory supplied
in the same workspace. No source Git revision was available. The package preserves
the source, tests, generated JSON/TXT artifacts, unsuccessful-attempt ledger, and
Magma handoff files; Python bytecode and cache directories were excluded.

This is retrospective producer evidence. The repository integration runs the
correctness suite but does not reclassify the retained arithmetic or Magma output
as independently reproduced or PCC-signed evidence. [pcc:unverified]

Key imported-file SHA-256 digests:

```text
REPORT_SOURCE  report.md
ASSESSMENT     artifacts/assessment.json
P224_QUARTIC   artifacts/p224_descended_quartic.json
P224_MAP       artifacts/p224_point_map_status.json
P256_DESCENT   artifacts/p256_descent_status.json
IMPLEMENTATION src/finite_field_theta.py
```

The exact digests are recorded in `IMPORT.sha256`.
