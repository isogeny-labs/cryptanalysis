# A 419,160-byte exact degree-13 function artifact replays both D79 prefixes across processes

One checked `H.build([13])` produced a content-addressed canonical JSON artifact containing all **28 rational Hecke function maps**, the rational j-function map, cusp and source identity. Four new checked-Sage processes loaded it without calling `H.build` and reproduced every visited fiber, signed cancellation and rank path at p8597 and p12197. An independent fresh build matched every decoded rational coefficient and the earlier six-invocation function digest.

| Stage or replay | Measured result |
| --- | ---: |
| Artifact build | 31,071 ms |
| Canonical encoding | 5.05 ms |
| Artifact size | 419,160 bytes |
| Independent fresh-build audit | 32,774 ms |
| Median artifact load across four processes | 15.47 ms |
| p8597 load and prefix replay, runs 1 and 4 | 676 ms, 616 ms |
| p12197 load and prefix replay, runs 2 and 3 | 1,011 ms, 995 ms |

The artifact SHA-256 is `131d0dc58a1a92a5c8f7aa2f79870dbd3b906accd17e019ee0e72d054ebc86ac`; its decoded function digest is `ebc29c5c9b4f3de35bc45afa4ac9f3b40db2f1a68c5a9912396a0ab67dca24ea`, matching [all six builds in the prior shared-build experiment](../hecke-d79-shared-build-20261027/RESULT.md). Each load process had `H.build` replaced by an exception-raising guard, then recomputed the full visited prefix: 12 sources and 4,984 signed patterns at p8597, 15 sources and 12,965 patterns at p12197, with final ranks 39 over Fq and 40 over Q. The inputs, artifact, builder, codec and load runner are all SHA-256 bound in [inputs.json](inputs.json) and [post_inputs.json](post_inputs.json).

The codec stores sorted coefficient maps as exact integer numerator/denominator pairs and rejects a wrong digest or filename, noncanonical JSON, duplicate or malformed function entries, nonreduced rationals, wrong source or degree, and an invalid cusp before returning Sage objects. The three exercised negative controls rejected changed bytes, pretty-printed JSON and a nonreduced rational as expected. The [independent build audit](audit-build.json), [four replay receipts](summary.json), [negative-control receipt](negative-controls.json), stdout/stderr and checked Sage runtime receipt are retained. The preliminary build itself includes a roundtrip equality check against the newly encoded artifact.

These timings exclude process launch and Sage import and are exploratory shared-host stage measurements. The 31-second construction is reusable preparation, while artifact loading was measured at roughly 15–17 ms in these four processes. The full prefix replay times include load, modular-polynomial setup and per-prime work, but use the frozen base-plus-direct preparation input. `candidate_id` and `target_online_ms` are null. The checked Lean rank certificates from [the prefix experiment](../hecke-d79-source-prefix-20261027/PROOF_MAP.md) apply to the identical rows; this cache adds an implementation result, not a new mathematical rank theorem.

The next implementation step is to expose the validated artifact through a versioned cache interface for other degree-13 consumers. That interface should use explicit validation exceptions throughout the decoder and retain a portable fallback to fresh `H.build([13])` when a cache artifact is absent or invalid.
