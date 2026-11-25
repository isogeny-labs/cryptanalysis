# L15/L16 — IC scaling at a fixed 31-bit largest factor (2026-11-24)

**Leads:** L15 and L16 in `crypto-autoresearcher/docs/open-leads-20261123.md`,
against `experiments/ic-fpstar-scaling-20261121/`.

**Question (L15):** the 2026-11-21 table mixed IC runs with Pohlig–Hellman-only
runs: at 52/56 bits the largest factor of `p-1` was below `2^24`, so no matrix
was built. Re-run 40–56 bits while **holding the size of the largest factor of
`p-1` fixed**.

**Question (L16):** the engine's cost lives in the sparse Lanczos solve over the
largest factor. Measure that step directly instead of inferring it from total
time.

## Construction: one fixed large factor

Set

```
q = 2^31 - 1 = 2147483647          (prime, 31 bits, fixed for every row)
p = k*q + 1                        (k even, all prime factors of k <= 683 < 2^24)
```

`IC_SMALL_Q = 2^24`, so every factor of `k` is handled by Pohlig–Hellman and the
only large-prime modulus is `q` in every run. All runs report
`mod 2147483647^1`, one Lanczos solve, and `status: ok` with `x` recovered.

| bits | `p` | `k` | factorization of `k` | `p-1` large factor |
|---:|---:|---:|---|---:|
| 40 | 601295421161 | 280 | 2³·5·7 | `2^31-1` |
| 44 | 8800387985407 | 4098 | 2·3·683 | `2^31-1` |
| 48 | 140789027897321 | 65560 | 2³·5·11·149 | `2^31-1` |
| 52 | 2322168556781569 | 1081344 | 2¹⁵·3·11 | `2^31-1` |
| 56 | 36565225532305471 | 17027010 | 2·3⁵·5·7²·11·13 | `2^31-1` |

All `k` factors are ≤ 683, so the 31-bit `q` is the unique factor above
`IC_SMALL_Q`.

## Measurements

`./build/ca ic --p P --g 3 --h 3^123456789 mod P --verbose`, one thread, one
seed, macOS. `p` is the constructed prime above, not the next prime after
`2^bits`.

| bits | factor base | unknowns | active rows×cols | Lanczos iters | sieve s | linalg s | total s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 40 | 125 | 926 | 848×465 | 465 | 0.001 | 0.014 | 0.015 |
| 44 | 196 | 1597 | 1458×766 | 766 | 0.001 | 0.040 | 0.041 |
| 48 | 303 | 2504 | 2167×1154 | 1154 | 0.001 | 0.089 | 0.090 |
| 52 | 452 | 4053 | 3232×1725 | 1725 | 0.003 | 0.199 | 0.202 |
| 56 | 669 | 6270 | 4805×2549 | 2549 | 0.004 | 0.437 | 0.441 |

All five runs: `verified_logs = factor_base`, `x = 123456789` recovered. Raw
output: `fixed31_results.json`.

### L15 reading

At a **fixed 31-bit largest factor**, over 40→56 bits:

- linear algebra grows from 0.014 s to 0.437 s (×31.2, or `2^(0.212·bits)`);
- the sieve stays at 0.001–0.004 s;
- the unknown count grows 926 → 6270 (×6.8), so linalg grows faster than the
  matrix dimension alone.

This replaces the 52/56-bit rows of the 2026-11-21 table, which were
Pohlig–Hellman timings (`lanczos_iterations = 0`, no matrix). At fixed large
factor, **the sparse solve dominates by 50–100x**, not the sieve. The old
"linalg dominates from ~52 bits" observation is therefore correct in direction
but was measured on the wrong path; this run establishes it on the IC path.

### L16 sparse-solve model

Per Lanczos iteration, `linalg_seconds / lanczos_iterations`:

| bits | µs / iteration | active cols |
|---:|---:|---:|
| 40 | 30.11 | 465 |
| 44 | 52.22 | 766 |
| 48 | 77.12 | 1154 |
| 52 | 115.36 | 1725 |
| 56 | 171.44 | 2549 |

Least-squares fit over these five points:

```
t_per_iteration ≈ 6.74e-8 s × active_cols      (R² = 0.99984)
```

and the iteration count is `0.41–0.50 × unknowns` (falling with size):

| bits | iters / unknowns |
|---:|---:|
| 40 | 0.502 |
| 44 | 0.480 |
| 48 | 0.461 |
| 52 | 0.426 |
| 56 | 0.407 |

So the measured model is

```
linalg ≈ (6.74e-8 s) × active_cols × iters,   iters ≈ 0.41–0.50 × unknowns.
```

This is a **machine-specific empirical fit**, not an asymptotic law. It says
the sparse matvec is linear in active columns at these sizes and that the
remaining growth comes from the iteration count and the factor-base growth.

## Exact commands

```sh
# from the cryptanalysis repo root
P=601295421161;          H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --verbose
P=8800387985407;         H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --verbose
P=140789027897321;       H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --verbose
P=2322168556781569;      H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --verbose
P=36565225532305471;     H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --verbose
```

`q` is fixed at `2^31-1`; `p = k*q+1` as in the table. The full machine-readable
rows (including `active_rows`, `active_cols`, `attempts`) are in
`fixed31_results.json`.

## What this establishes

- A controlled IC scaling series at a **fixed 31-bit largest factor** for
  40/44/48/52/56 bits, all on the IC path with one Lanczos solve.
- The 52/56-bit rows of the 2026-11-21 note are Pohlig–Hellman-only and must
  not be used as IC linalg timings.
- At fixed large factor, the sparse solve dominates the sieve by 50–100x, and
  its measured per-iteration cost is linear in active columns
  (`6.74e-8 s × cols`, R²=0.99984).

## What this does not establish

- No asymptotic claim: five sizes, one seed, one thread, one machine (macOS),
  16-bit range, one fixed factor size (31 bits).
- No multi-thread, 64-bit, `--method rexp`, or multiple-large-factor data.
- No cryptographic-`p` claim.
- The fit constant is machine-specific; the iteration-count ratio is empirical.
- Not a `d_reg` or Semaev/F4 measurement; this is `F_p*` index calculus.
