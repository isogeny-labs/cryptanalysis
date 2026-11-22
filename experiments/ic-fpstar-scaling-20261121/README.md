# F_p* index calculus in this repo: scaling and phase split (2026-11-21)

**Status:** measurement note, unreviewed. Single-thread, single machine, one
seed per size. Not an asymptotic claim.

## Scope — what this repo's IC actually is

`src/indexcalc.c` + `tests/test_indexcalc.c` implement **index calculus in
F_p\*** (multiplicative group): a sieve over `(c1, c2)` with trial division by a
prime factor base, a large-prime graph step, and sparse linear algebra
(Lanczos). It is *not* ECDLP index calculus: Semaev summation-polynomial work
lives in the sibling repo `/Volumes/SSD990/crypto` (`cryptanalysis/ec_index_calculus.rs`,
`f4_fp.rs`, `gaudry_cubic.rs`). Keeping the two straight matters, because the
two have different failure modes and different literature.

## Build

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCA_CUPQC=OFF
cmake --build build -j 8
```

`CA_CUPQC=ON` (the default) aborts configuration on a non-Linux-CUDA host;
`-DCA_CUPQC=OFF` is required on macOS.

## Measurements

`./build/ca ic --p P --g 3 --h 3^x mod P`, one thread, x fixed at 123456789,
p the next prime above 2^bits. Raw output in `results.json`.

| bits | factor base | relations | sieve (s) | linalg (s) | total (s) |
|---:|---:|---:|---:|---:|---:|
| 40 | 143 | 1355 | 0.001 | 0.006 | 0.007 |
| 44 | 222 | 2259 | 0.002 | 0.020 | 0.022 |
| 48 | 342 | 3180 | 0.003 | 0.030 | 0.033 |
| 52 | 510 | 5032 | 0.005 | 0.037 | 0.042 |
| 56 | 757 | 7703 | 0.007 | 0.118 | 0.125 |

Every run verified: `status: ok`, recovered `x` equals the planted value, and
100% of factor-base logs verified (`verified_logs == factor_base`).

**Local fit:** `total ≈ p^0.231` over these five points (log–log least
squares). That is a *local* slope over a 16-bit span, not the L[1/3] exponent;
the subexponential exponent grows as `p → ∞` and five points cannot separate
the models.

## Observations worth carrying forward

1. **Linear algebra dominates from ~52 bits.** At 56 bits, linalg is 17× the
   sieve (0.118 s vs 0.007 s). Any further engineering should target the sparse
   solve, not the sieve — the opposite of the usual ECDLP index-calculus
   bottleneck.
2. **`lanczos_iterations` reports 0 at 52 and 56 bits** while the solve still
   succeeds and the logs verify. Either the counter is not propagated for the
   larger paths or a different solver is chosen silently. Worth a look before
   the field is used as a cost input.
3. **Factor base grows ~0.75 per bit** (143 → 757 over 40 → 56 bits), i.e.
   roughly `p^{0.19}`, consistent with a Morrison-style L[1/2]-region
   parameterisation rather than the L[1/3] NFS-style one. If the intent is a
   large-p engine, the parameterisation (`--B`, `--C`) is the first thing to
   revisit.
4. **The engine is fast at these sizes** (0.125 s at 56 bits). The interesting
   regime starts where linalg memory, not time, becomes binding.

## Not done here

- Threads (`--threads`), `--method rexp` comparison, and the large-prime graph
  variant are untested in this note.
- No 64-bit point; `p < 2^64` is the implementation's field limit.
- No comparison against the repo's published IC bounds; that is a separate
  adjudication.
