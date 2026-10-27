# Validated degree-13 function cache interface

The versioned interface loads the pinned 419,160-byte rational function artifact with explicit validation errors. On a valid artifact it returns the exact 28 degree-13 functions with zero `H.build` calls. With fallback policy, a missing or digest-invalid artifact triggers exactly one fresh `H.build([13])`; strict policy rejects either input with zero builds. The cached and rebuilt functions reproduce the frozen p8597 and p12197 source-prefix fibers, cancellations, and rational rank paths.

The identity is the source SHA-256 `7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb`, artifact SHA-256 `131d0dc58a1a92a5c8f7aa2f79870dbd3b906accd17e019ee0e72d054ebc86ac`, and decoded function digest `ebc29c5c9b4f3de35bc45afa4ac9f3b40db2f1a68c5a9912396a0ab67dca24ea`. The input plan fixes paths, source and runner hashes, two frozen prefix receipts, policies, and a 1,800-second cap. These ordinary-host setup timings are diagnostics; the runs do not measure a target-dependent IC interval.

| Run | Status / cause | Build calls | Load ms | Build s | Prefix sources | Rational rank / mod-q rank |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| hit-8597 | CACHE_HIT | 0 | 31.844 | 0 | 12 | 40 / 39 |
| hit-12197 | CACHE_HIT | 0 | 31.754 | 0 | 15 | 40 / 39 |
| missing-8597 | FALLBACK_MISSING / CACHE_MISSING | 1 | 0.013 | 37.363 | 12 | 40 / 39 |
| invalid-12197 | FALLBACK_INVALID / ARTIFACT_DIGEST_MISMATCH | 1 | 0.503 | 32.935 | 15 | 40 / 39 |
| strict-missing-12197 | REJECTED_MISSING / CACHE_MISSING | 0 | — | — | — | — |
| strict-invalid-8597 | REJECTED_INVALID / ARTIFACT_DIGEST_MISMATCH | 0 | — | — | — | — |

Each run has a JSON receipt with build degrees, phase times, peak RSS, and the replayed rank path. The invalid fixture differs by one byte and is retained under `fixtures/`. The original artifact is immutable. A separate checked-Sage process rebuilt all functions and compared every decoded coefficient, cusp, and function digest. Under `./sage -python -O`, the decoder rejected a nonreduced rational and altered source hash via explicit exceptions; see `audit-optimized.json`. The original v1 codec remains frozen; this interface uses `codec_v2.py`.

Reproduce with `./sage --runtime-info` and `gtimeout 1800 ./sage -python experiments/hecke-d79-cache-interface-20261027/run_case.py --run-id <id>`, followed by `gtimeout 1800 ./sage -python -O experiments/hecke-d79-cache-interface-20261027/audit_v2.py` and `python3 experiments/hecke-d79-cache-interface-20261027/verify.py`. The saved runtime receipt is `sage-runtime-info.txt`.

The first version of `verify.py` expected mod-q rank 40 and failed on `hit-8597`; it was corrected to compare both ranks with the hash-pinned prefix result. Both frozen prefix results have rational rank 40 and mod-q rank 39. Final verification passes all six run receipts.

No new mathematical proposition is introduced by the cache interface. The rank evidence and Lean proof map remain in the earlier D79 prefix and support-four experiment records. The next implementation step is to integrate `resolve` into a consumer that needs repeated rational function setup, preserving the same pinned source and artifact identity.
