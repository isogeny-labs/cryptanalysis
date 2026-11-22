# CT319 — cold-process receipt-to-cost binding (preregistered 2026-11-22)

**Standing:** source-only, [pcc:unverified]. Continuation on existing draft cryptanalysis PR #1920 (CT318). No native Jacobian execution or credential use.

## Falsifiable admission defect

CT318 requires per-run raw stdout and a receipt file with the SHA-256 claimed in the CT315 panel, but CT317 only checks the receipt file's digest, not its *contents*. Consequently, an otherwise passing panel can change `external_wall_ns`, `peak_rss_kib`, `binary_sha256`, and `argv_sha256` without adjusting any receipt. It can then print a provisional candidate/baseline ratio unmoored from its own external process record. This is a provenance/consistency flaw, not evidence that any original producer was compromised.

## Contract frozen before implementation

1. Compose the original CT318 joint audit unchanged. Then for **every run** require a CT304 successful bounded-process receipt (exact CT304 schema) at `<raw-root>/<run-id>.receipt.json`, raw stdout and stderr at `<run-id>.stdout` and `<run-id>.stderr`, a retained per-arm executable at `<raw-root>/<arm>.binary`, and one supplied literal fixture byte file. Use the original `ct304_execution_receipt_gate.check_capture` for byte hashes/lengths, executable bytes, host identity/affinity, success and fixture SHA-256/Git blob, not a reimplemented ad-hoc substitute.
2. Match the CT315 row to the CT304 record: exact `run_id`, `stdout_sha256`, `binary_sha256`, `external_wall_ns`, `peak_rss_kib` (strict positive integer), `host` to receipt `host.hostname`, and `cpu_affinity` to receipt `host.cpu_affinity`. Define `argv_sha256` as SHA-256 of UTF-8 canonical JSON of receipt `argv`, serialized with Python `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` and *no newline*. The recorded `argv[0]` must equal the precise retained executable path. Reject deviations or incomplete files, even if CT315 and CT317 alone pass.
3. A CT304 record's `run_id` is exactly 32 lowercase hexadecimal characters; keep that rule rather than grandfathering CT318's illustrative `toy-*` IDs. CT319 uses new synthetic 32-hex IDs. Reject a missing or mismatched receipt, invalid stderr/executable bytes, nonzero exit, invented RSS, wall-time reprice, command tampering and changed fixture. Preserve the raw receipt hash requirement in CT317; no canonicalizing its input bytes.
4. Self-tests first demonstrate that a valid CT318 source panel can have its wall/RSS/argv claims mutated **without** changing its receipt; show CT319 correctly refuses these same mutations. Add a synthetic all-28-run positive and two signed-direction provisional cost cases. Repeat under normal Python and `-O`, with zero original model executions.
5. Do not change CT315, CT317, CT318, original six S3 objects, 695/701 fixtures, historical tool/config pins or PCC. Do not perform EKS Spot, S3 access, real native execution, protected merge, or report an actual speedup.

## Limitations and next decisive experiment

CT304 receipts are producer-supplied; even byte-for-byte binding does **not** authenticate actual OS execution, clock accuracy, sourcing of `source_sha256`, transfer arithmetic or model provenance. GNU-time CT316 reports one child `ru_maxrss`, not necessarily an entire process tree, and a future panel must explicitly account for subprocess families and resource tiers.

Admit real original six-object S3 custody only under separately authorized coherent tool/config + STS and no-prefetch approval. Replay complete 695/701 native maps, meter C169/C13a/C13b/D/N2_actual and perform genuine seven-arm same-host cold single-target solves, with all phases, verified Q=[k]P, memory/uncertainty and strongest retained lift/rho/BSGS/frontier IC. Require independently reproduced, signed PCC before any speedup claim.

[pcc:unverified]
