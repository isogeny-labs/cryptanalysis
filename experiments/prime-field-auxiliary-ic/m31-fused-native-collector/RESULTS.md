# Fused native M31 collector: charged full-pipeline result

Status: local producer evidence `[pcc:unverified]` on Apple M4 Pro (Mac16,7), 2026-11-25. The implementation is a Rust full pipeline with a C++/ARM64 NEON candidate scan FFI. It changes no factor-base construction, exact indexed payload map, relation equation, walk RNG, elimination, or answer check. Base commit before this experiment: `8507bc7e781360898130d9494c61cb2babeda45a`.

The C++ function batches 500 denominator inversions, computes both signed affine sums, tests the same 512 KiB high-bit x bitmap, and returns bitmap-positive `(signed index, point key)` candidates in order. Rust performs the exact first-payload index lookup and all subsequent checks. Exceptional denominators and the identity point use the Rust path. Both binaries link the same native library; the control never invokes it.

## Checks before timing

- Existing C ABI inverse checker: 1,097,730 outputs, including edge values, lengths, in-place and out-of-place buffers, and sentinels.
- Independent Python group-law checker: all 1,000 signed output keys and their order on each frozen public auxiliary and plain basis with an all-ones bitmap; exceptional denominator returns the fallback sentinel.
- Audit binary: for every walk state through a full solve at each tested seed on both bases, native and Rust returned the same first exact hit. The complete sorted `(point key, first payload)` maps were byte-identical: SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` auxiliary, `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` plain.
- Every timed pair had the same regenerated public basis digest, scalar `123456789`, trial count, relation count and table entry count. Each answer was checked by multiplying the generator. No failures or censored arms occurred.

## Charged timings

Each value is the median of 24 paired native/control ratios for the named basis and metric. Seconds are separate arm medians, so their quotient need not equal the median paired ratio. Each arm charges basis regeneration and input writing, process startup, table and bitmap building, collection, elimination, verification, output parsing and exit. CPU includes parent plus child. Builds and preflight preceded timing; caches were not flushed.

| Panel / basis | Control wall s | Native wall s | Paired wall ratio | Wall wins | Control CPU s | Native CPU s | Paired CPU ratio | CPU wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Initial seeds 0–2 / auxiliary | 0.06149 | 0.05417 | 0.8801 | 24/24 | 0.06065 | 0.05356 | 0.8790 | 24/24 |
| Initial seeds 0–2 / plain | 0.05090 | 0.04435 | 0.8713 | 24/24 | 0.05002 | 0.04347 | 0.8718 | 24/24 |
| Confirmation seeds 3–5 / auxiliary | 0.06586 | 0.05738 | 0.8714 | 24/24 | 0.06511 | 0.05648 | 0.8680 | 24/24 |
| Confirmation seeds 3–5 / plain | 0.05538 | 0.04713 | 0.8546 | 24/24 | 0.05444 | 0.04672 | 0.8544 | 24/24 |

The native scan was called for every trial in the timed runs (5,652–6,715 calls per arm); no fallback occurred. The observed benefit is about 12–15% of this charged full Rust pipeline, including the unchanged setup and elimination. The first run used shuffle seed 112587 inherited from the prior runner; `PROTOCOL.md` had specified 112593. This deviation was discovered and recorded before confirmation. The separate confirmation froze and used shuffle seed 824213 with fresh walk seeds, and is the primary performance evidence.

Raw arm records: `RAW.csv`, `CONFIRMATION.csv`. Reproduction commands and acceptance gates: `PROTOCOL.md`, `CONFIRMATION_PROTOCOL.md`, `replay.py`. Source SHA-256: `main.rs` `1f0a77a8e8134c57248571637f79d118ad74d593c51fa3814c20774d1cf0a90c`; `scan.cpp` `ddd19577d4c57741a290548d00a0daaafc6ce06cfc1491869ef6754761e42928`. These hashes are for the timed source. The runner change between panels only exposed a seed override and corrected its default shuffle.

This demonstrates a local finite-field implementation speedup on frozen same-target public M31 fixtures, not a new complexity bound. It has no Lean refinement theorem connecting the C++ ABI to the mathematical scan. The existing Lean field identities do not prove the FFI implementation or wall-clock behavior. An independent signed review and matched rho comparison remain required before any stronger cryptanalytic claim.
