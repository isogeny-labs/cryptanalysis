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

| bits | factor base | relations | sieve (s) | linalg (s) | total (s) | path |
|---:|---:|---:|---:|---:|---:|---|
| 40 | 143 | 1355 | 0.001 | 0.006 | 0.007 | IC (36-bit factor of p-1) |
| 44 | 222 | 2259 | 0.002 | 0.020 | 0.022 | IC (28-bit factor) |
| 48 | 342 | 3180 | 0.003 | 0.030 | 0.033 | IC (32-bit factor) |
| 52 | 510 | 5032 | 0.005 | 0.037 | 0.042 | **Pohlig–Hellman only** |
| 56 | 757 | 7703 | 0.007 | 0.118 | 0.125 | **Pohlig–Hellman only** |

**Correction, 2026-11-22.** The first version of this table presented all five
rows as IC measurements. That is wrong for the last two. `IC_SMALL_Q` is `2^24`
(`src/indexcalc.c:17`): prime factors of `p-1` at or below that are handled by
Pohlig–Hellman, and the index-calculus matrix is never built. For the primes
chosen at 52 and 56 bits the largest factor of `p-1` is 987,127 and 14,557,303
respectively — both below `2^24` — so those runs never entered the IC path.
That is also the explanation for the earlier "quirk" that
`lanczos_iterations` reported 0 at those sizes: no Lanczos solve ran.

**What the IC path actually costs.** A 48-bit safe prime
(`p = 2q+1`, q a 47-bit prime, so the whole subgroup is one large factor) did
**not finish within 9 minutes**, against 0.033 s for the 48-bit prime whose
large factor is 32 bits. The practical variable is the size of the largest
prime factor of `p-1`, not the size of `p`: the engine's linear algebra runs
over that factor's modulus. Any scaling claim must hold `log(largest factor)`
fixed or report it alongside the bit size.

## Observations worth carrying forward

1. **Linear algebra dominates from ~52 bits.** At 56 bits, linalg is 17× the
   sieve (0.118 s vs 0.007 s). Any further engineering should target the sparse
   solve, not the sieve — the opposite of the usual ECDLP index-calculus
   bottleneck.
2. **`lanczos_iterations` is 0 at 52 and 56 bits because the relation matrix
   is never built for those primes.** `p - 1` is 2²⁴-smooth there
   (2²·3⁴·23·612229·987127 and 2⁴·3·7²·61·34501·14557303), so every
   factor-base log comes from Pohlig–Hellman and the sparse solve is
   skipped; only the 40–48-bit primes have a factor above `IC_SMALL_Q`.
   That makes the 52/56-bit `linalg_seconds` a Pohlig–Hellman timing, not a
   matrix timing, and the fit in the table mixes the two paths. `ca ic` now
   prints `matrix_used` (0/1) beside `lanczos_iterations` so the path is
   visible; the comparison table should be rerun on primes whose `p - 1`
   has a large factor before the linalg share is used as a cost input.
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

## Large-prime graph structure (2026-11-22)

`build_graph_matrix` treats relations with one or two large primes as edges and
solves each connected component with a spanning-tree propagation plus one
auxiliary column per cyclic component. Instrumented with
`CA_IC_GRAPH_DEBUG=1` (prints nodes / components / cyclic / trees / edges):

| p bits | large-prime nodes | components | cyclic | tree | edges | emitted columns |
|---:|---:|---:|---:|---:|---:|---:|
| 40 | 951 | 1 | 1 | 0 | 1355 | 144 (143 fb + 1) |
| 44 | 1601 | 1 | 1 | 0 | 2259 | 223 (222 fb + 1) |
| 48 | 2551 | 1 | 1 | 0 | 3180 | 343 (342 fb + 1) |

**The graph is a single giant component at every size tested**, so:

1. Tree components do not arise in this regime; a "skip tree components" change
   is a correctness/cleanliness improvement (committed, verified by
   `test_indexcalc`: 859,159 checks) but **measurably a no-op here**.
2. The auxiliary-column count is 1, so the matrix is essentially
   `nfb + 1` columns — the large-prime step is not inflating the linear algebra.
3. The propagation cost is `O(nodes x nfb)` (an expression vector per node):
   ~20 MB and ~5M int operations at 56 bits. Small next to the Lanczos solve.

Conclusion: **do not optimize the graph step for speed in this engine.** The
cost is the sparse solve over the largest factor of `p-1`. If a regime with
many small components is ever wanted (fewer relations per large prime), the
tree-skip and the per-component parallelism are already in place conceptually;
neither would help the current workload.

## L15 — scaling at fixed log(largest factor of p-1) (2026-11-24)

The corrected table in §"Correction" leaves three genuine IC rows at different
large-factor sizes, so it cannot separate `log p` from `log(largest factor)`.
This run holds the large factor fixed: `p = m*q + 1` with `q` a 28-bit prime
(134,217,757) and `m ~ 2^(bits-28)`, so `q` is the largest prime factor of
`p-1` at every size. Driver: `run_l15.py`.

| bits | p | m | fb | relations | sieve (s) | linalg (s) | total (s) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 40 | 549,755,932,673 | 4,096 | 125 | 1,072 | 0.001 | 0.003 | 0.004 |
| 44 | 8,801,195,197,519 | 65,574 | 196 | 1,964 | 0.001 | 0.007 | 0.008 |
| 48 | 140,737,518,764,033 | 1,048,576 | 303 | 2,885 | 0.001 | 0.018 | 0.020 |
| 52 | 2,251,800,300,224,513 | 16,777,216 | 452 | 4,493 | 0.003 | 0.052 | 0.054 |

All runs: `status: ok`, planted log recovered, 100% of factor-base logs
verified, and `ic_path: true` (the relation matrix and Lanczos solve ran).

**Local fit: `total ~ p^0.315`** over 40→52 bits at fixed 28-bit large factor.

**Interpretation, with its limit stated:** the exponent here is a local slope
over a 12-bit span at one fixed factor size, not an asymptotic law. What it
does show is that with the large factor held fixed the engine is cheap and
smooth (4 ms → 54 ms) and that the linear algebra is the growing term
(0.003 s → 0.052 s, ~17x, while the sieve grows ~3x). Compare the earlier
48-bit safe prime (47-bit large factor) which did not finish in 9 minutes:
**the large-factor size, not the field size, is the dominant cost variable.**

Next: repeat at q_bits = 32 and 36 to fit the exponent as a function of
log(largest factor) — that is the number a cost model actually needs.

## L16 — cost as a function of the large factor's size (2026-11-24)

L15 held `q` fixed and varied `p`. This run fixes `p` at 56 bits and varies
`q_bits = log2(largest prime factor of p-1)`. Driver: `run_l16.py`; raw output
in `results_l16.json`.

| q_bits | q | fb | relations | sieve (s) | linalg (s) | total (s) | lanczos iters |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 524,309 | 669 | 6,837 | 0.004 | 0.013 | 0.018 | **0** |
| 24 | 8,388,617 | 669 | 6,658 | 0.004 | 0.024 | 0.028 | **0** |
| 28 | 134,217,757 | 669 | 6,705 | 0.004 | 0.206 | 0.210 | 1,340 |
| 32 | 2,147,483,659 | 669 | 6,696 | 0.004 | 0.113 | 0.117 | 669 |
| 36 | 34,359,738,421 | 669 | 6,656 | 0.004 | 0.120 | 0.124 | 670 |

**The first two rows are not IC runs.** `q <= 2^24 = IC_SMALL_Q`, so the engine
solves by Pohlig–Hellman and never builds the matrix (`lanczos_iterations = 0`).
Any fit that includes them is meaningless — the "q^0.19" reported by the driver
is exactly that mistake, and is withdrawn here.

**Among the three genuine IC rows there is no growth:** 0.21 s at q_bits = 28,
0.117 s at 32, 0.124 s at 36. The 28-bit row is the *slowest*, with
`lanczos_iterations = 1340` against a factor base of 669 (two attempts or two
moduli), which looks like an attempt-count artifact rather than a size effect.

**Together with the 47-bit safe prime (did not finish in 9 minutes), the honest
statement is that this engine's cost is not a smooth function of `log q` in the
tested range: it is flat from 28 to 36 bits, then jumps somewhere between 36 and
47 bits.** A cost model needs that threshold located, not an exponent fitted
through five single-seed points.

Next: repeat each cell >= 5 times (attempt counts vary), and bracket the
threshold with q_bits = 40, 44 at fixed p = 56 bits.
