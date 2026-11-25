# Cache-resident x prefilter versus paired control

The protocol in `BLOOM_PROTOCOL.md` was frozen before measurement. The candidate stores one hashed bit per inserted x in a 128 KiB bitmap. A cleared bit allows the collector to skip ordinate materialization; a set bit still performs the ordinary exact point-key lookup. The bitmap is charged during table construction. The control and candidate use the same sign-packed index, one-multiply slot hash, validated shared-x paired arithmetic, direct pair rows, relation walk and modular elimination.

The audit phase reconstructed both frozen 500-point bases and found byte-identical complete sorted `(point key, first payload)` maps for control and candidate (auxiliary SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879`, plain `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`). A subsequent audit checks every occupied x slot has its bitmap bit set. Every one of 96 matched pairs across two panels agreed on basis digest, verified scalar `123456789`, trial count, relation count and table size. No arms failed or were censored.

| Panel | Basis | Paired control wall median ms | Bitmap wall median ms | Median paired control/bitmap wall ratio | Bitmap wall wins | Median paired CPU ratio | Bitmap CPU wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| First | Auxiliary | 187.501 | 153.784 | 1.2597 | 19/24 | 1.2616 | 23/24 |
| First | Plain | 180.641 | 135.213 | 1.3453 | 23/24 | 1.3357 | 24/24 |
| Confirm | Auxiliary | 188.688 | 153.493 | 1.2554 | 20/24 | 1.2801 | 23/24 |
| Confirm | Plain | 172.308 | 126.732 | 1.3484 | 24/24 | 1.3496 | 24/24 |

CPU arm medians in order control/bitmap were 179.671/143.522 ms and 166.810/125.838 ms in the first panel, 180.470/144.755 ms and 158.835/123.738 ms in confirmation (auxiliary/plain). Table-build-only paired ratios were below one for three of four rows, so the gain comes from the collector rather than setup. The charged timer includes basis generation, input writing, table build, relation collection, elimination, answer verification and process exit. Compilation, frozen JSON load and complete map audit precede the timer. OS caches were not flushed. Ratios are medians of matched ratios and need not equal ratios of arm medians.

`Bloom.lean` proves that marking the bit for every inserted x cannot reject an inserted x, even with hash collisions. It composes that invariant with `XFilter.lean` to prove preservation of the first accepted payload under the explicit premise that every successful exact lookup has an inserted x. The proof does not verify the Rust machine code, memory layout, or runtime. The Rust audit checks that premise for the two frozen tables, and the full collector equality checks cover the measured walks.

This is a reproducible local same-target gain on one shared Apple M4 Pro host. It is not a complexity improvement or a claim about other targets, native x86, GPUs or independent replay. [pcc:unverified]

Raw CSV SHA-256: first `a5f7f0edc2b2b886654f5478bfea0c05738e0e9e38eb73287c2f8fbf5830dc0c`, confirmation `402e923850e4fef124e3d75c929ae48d101a9e57c7234247c701bb842136f8b7`.
