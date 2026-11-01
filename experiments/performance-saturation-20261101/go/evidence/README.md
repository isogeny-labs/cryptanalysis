# Remote build evidence

This directory retains byte-identical copies of the redacted HTTP receipts and
result archives from the pre-measurement RunPod build attempts.  The v3-v5
archives contain only `.runpod-batch` metadata and no build output.  The v6
archive contains the successful build-only manifest and two executables, but no
correctness test, fingerprint, allocation, or timing row.  The source files
under `/workspace/.benchmarks` were not modified.

| Attempt | Pod | Receipt SHA-256 | Archive SHA-256 | Terminal gate |
| --- | --- | --- | --- | --- |
| v3 | `12qpeygj0synuk` | `b3642d987aa9a2b34ff263a100568bea4a1bc8e17abad892f3801e91bba2dfb5` | `4d74adbf09834eb7f6f4ad6531d5460b284f9529ae59d4726eb0abbd5946fedf` | noncontiguous 32-CPU affinity rejected |
| v4 | `0pbdktc657sz3t` | `c91ed9dfdaef89ce97543c276ad9307a7d4f8f15b31be14390d8aad205cdea65` | `75608ff4668bfa1a5db4bfd8efa956528becdb01838a8f7777d05ef3de2d0ac0` | shallow-checkout parent identity rejected |
| v5 | `2owqoma1tb5yf0` | `a38be64592fa852a485a00a2a13e166b86b838e013f6c2ef74ba9d28e99f76b1` | `14bdff42c402f4d2cb8e37eebcac6883bf734957e7c58312292cb6759472a5cd` | decimal `memory.max` incorrectly compared with 64 GiB |
| v6 | `6xr0x0fwky4yyd` | `7ce7c502f8b8fe89aa60e168b6c92b4b08ed798b3a1f4466e26ff9cc32e1e39d` | `4bb8cff1e41a09119cfcded20ac4c671a0cb470afd809f7341e755971506f99e` | build-only success; artifact gate retained |

Every receipt records `cleanup.delete_requested=true` and
`cleanup.absence_verified=true`.  V3-v5 record nonzero return codes.  V6 records
return code zero and binds build manifest SHA-256
`540f67c53a271d36862a906fb29f43ed88728703b5ad27abeeb004727089fcbd`,
baseline executable SHA-256
`a6519b5c68f41690ae1e689457122c6787cea1de0cc8be272eafcb34e5269720`,
and candidate executable SHA-256
`b688b1a7694acda87bb31398611f158619a71dd529090abb9793ce8ac6e1293f`.
Its original controller disconnected, so the committed recovery tool retrieved
the original pod result without creating another allocation; the recovery
receipt records that fact.  All four attempts remain immutable evidence and
none is itself a scientific distribution.
