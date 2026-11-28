# Metal affine candidate admission, preliminary

Status: correctness admission passed for the checked public B195 signed-pair construction; end-to-end admission remains open. These are producer-run local measurements, not an independent speedup claim. [pcc:unverified]

`admission.swift` builds the first 195 liftable x-coordinates on the public M31 curve, enumerates the same i<=j, plus/minus pair rule as `PairIndex`, canonicalizes by y, and creates 38,025 distinct pair entries. It evaluates `Q ± entry` for 1, 8 and 64 lanes, replacing the first four rows with vertical, tangent, left-identity and right-identity cases. All GPU outputs equalled the Swift affine reference point by point. An independent Rust `Curve<31>` run produced matching ordered x/y FNV digests for each size. The Rust digest comparison is a strong replay check, not a formal proof of identical implementation semantics.

| Lanes | Candidates | GPU compile, buffer, dispatch, wait | GPU dispatch and wait | Swift affine | Mismatches | Rust/Swift digest |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 76,050 | 5.168 ms | 2.962 ms | 6.562 ms | 0 | 8369032597423072703 |
| 8 | 608,400 | 8.530 ms | 5.000 ms | 55.339 ms | 0 | 12732938990286056998 |
| 64 | 4,867,200 | 39.941 ms | 18.818 ms | 452.207 ms | 0 | 429071123967448180 |

The independent Rust solver control on the same public Q with interval B195, m4, seed 2911332506172719186, lanes 64 and chunk 16384 reported 608 queries, 192 relations, 332.799 ms decomposition, 334.385 ms online and 0.853 ms pair-index construction. Its replayed answer was 264620306. This implies about 0.55 ms decomposition per walk query and about 33 ms per 64-lane round, but per-query and per-round numbers are derived from one run and are not a matched GPU end-to-end comparison. The GPU 64-lane admission did 40 ms of charged GPU setup and work on 64 distinct, constructed public points; the native control uses its actual dependent walk points and can exit early. The tested GPU path therefore has not cleared the 1.15× native component gate. [pcc:unverified]

The first modular-multiply microbenchmark is superseded as a cost predictor: point inversion, buffers, and dispatch materially change the result. The next concrete route is a persistent Metal pipeline with an x-bitmap filter that returns only hit indices, then a Rust differential audit against all actual walk points. That should be costed before any end-to-end claim or Lean refinement proof. A Lean theorem about timing would have no bearing on this result.

Reproduce locally on Apple Metal: `swiftc -O admission.swift -o /tmp/m31-metal-admission`, run it with `195 1`, `195 8` and `195 64`; compile `verify.rs` against the current `prime_field_auxiliary_ic` rlib and compare `digest`. The repository control is `m31-fast --qx 1767503692 --qy 244402461 --seed 2911332506172719186 --columns 195 --summands 4 --method indexed --base interval --lanes 64 --chunk 16384 --max-queries 100000 --max-ms 5000 --profile`.
