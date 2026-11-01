# Remote build failure evidence

This directory retains byte-identical copies of the redacted HTTP receipts and
result archives from the three pre-measurement RunPod build failures.  The
archives contain only `.runpod-batch/log.txt`, `job-status.json`, `source.json`,
and `files.sha256`; none contains a build output or benchmark data.  The source
files under `/workspace/.benchmarks` were not modified.

| Attempt | Pod | Receipt SHA-256 | Archive SHA-256 | Terminal gate |
| --- | --- | --- | --- | --- |
| v3 | `12qpeygj0synuk` | `b3642d987aa9a2b34ff263a100568bea4a1bc8e17abad892f3801e91bba2dfb5` | `4d74adbf09834eb7f6f4ad6531d5460b284f9529ae59d4726eb0abbd5946fedf` | noncontiguous 32-CPU affinity rejected |
| v4 | `0pbdktc657sz3t` | `c91ed9dfdaef89ce97543c276ad9307a7d4f8f15b31be14390d8aad205cdea65` | `75608ff4668bfa1a5db4bfd8efa956528becdb01838a8f7777d05ef3de2d0ac0` | shallow-checkout parent identity rejected |
| v5 | `2owqoma1tb5yf0` | `a38be64592fa852a485a00a2a13e166b86b838e013f6c2ef74ba9d28e99f76b1` | `14bdff42c402f4d2cb8e37eebcac6883bf734957e7c58312292cb6759472a5cd` | decimal `memory.max` incorrectly compared with 64 GiB |

Every receipt records `cleanup.delete_requested=true` and
`cleanup.absence_verified=true`.  Each archive records a nonzero return code
and the exact source and command identities used by that attempt.  These files
are immutable failure evidence and are excluded from scientific distributions.
