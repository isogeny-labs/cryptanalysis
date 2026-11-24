# L17 — `--method rexp` at a fixed 31-bit largest factor (2026-11-24)

**Lead:** L17 in `crypto-autoresearcher/docs/open-leads-20261123.md`
(`--method rexp` and 64-bit regimes untested).

## Setup

Same controlled primes as L15/L16: `p = k·q + 1`, `q = 2^31−1` fixed, `k`
2²⁴-smooth, so the only large factor is 31 bits. One thread, one seed,
`x = 123456789`. Command:

```sh
./build/ca ic --p P --g 3 --h 3^123456789 --method rexp --verbose
```

The engine auto-sizes the factor base; `rexp` uses `B × 3/2` relative to the
linear sieve, so the two methods do **not** have the same factor base. That is
part of the comparison, not a controlled same-B run.

## Results

| bits | method | factor base | unknowns | relations | verified logs | sieve s | linalg s | total s |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 40 | lsieve | 125 | 926 | 1100 | 125/125 | 0.001 | 0.014 | 0.015 |
| 40 | rexp | 176 | 176 | 257 | 163/176 | 0.005 | 0.002 | 0.007 |
| 44 | lsieve | 196 | 1597 | 1906 | 196/196 | 0.001 | 0.040 | 0.041 |
| 44 | rexp | 278 | 278 | 385 | 262/278 | 0.014 | 0.004 | 0.017 |
| 48 | lsieve | 303 | 2504 | 2920 | 303/303 | 0.001 | 0.089 | 0.090 |
| 48 | rexp | 430 | 430 | 577 | 412/430 | 0.037 | 0.008 | 0.045 |
| 52 | lsieve | 452 | 4053 | 4456 | 452/452 | 0.003 | 0.199 | 0.202 |
| 52 | rexp | 646 | 646 | 769 | 582/646 | 0.086 | 0.016 | 0.103 |
| 56 | lsieve | 669 | 6270 | 6791 | 669/669 | 0.004 | 0.437 | 0.441 |
| 56 | rexp | 950 | 950 | 1089 | 858/950 | 0.238 | 0.028 | 0.267 |

All ten runs recover `x` and return `status: ok`.

## Reading

- At fixed 31-bit largest factor, `rexp` is **≈2.0–2.2x faster in total time**
  than the linear sieve over 40–56 bits (0.007 vs 0.015, 0.017 vs 0.041,
  0.045 vs 0.090, 0.103 vs 0.202, 0.267 vs 0.441 s).
- The speed comes with a **larger factor base** (`B×3/2`) and **incomplete log
  verification** (163/176 … 858/950, always > half). The solve still succeeds.
  `rexp` does not build the `nfb + 2C + 1` column matrix of the sieve; its
  linear algebra is over the factor-base columns only, which is why linalg is
  smaller.
- The linear sieve's linalg dominates its total at ≥48 bits; `rexp` moves the
  cost into relation collection (sieve 0.238 s vs linalg 0.028 s at 56 bits).
  The crossover is a method choice, not a universal law.

## 64-bit regime

The implementation rejects `p ≥ 2^63` (`src/indexcalc.c`, `p >> 63` guard), so a
true 64-bit point cannot be run with this engine. The highest controlled point
tested here is 56 bits. A 60/62-bit point could be built the same way
(`p=kq+1`, `k` smooth) but is not run in this note.

## Exact commands

```sh
P=601295421161;      H=$(python3 -c "print(pow(3,123456789,$P))"); \
  ./build/ca ic --p $P --g 3 --h $H --method rexp --verbose
# repeat for 8800387985407, 140789027897321, 2322168556781569, 36565225532305471
```

Raw rows: `rexp31_results.json`.

## What this establishes

- `rexp` is a viable faster method at the tested fixed-largest-factor cells
  (40–56 bits), at the cost of a larger base and partial log verification.
- The 64-bit regime is unsupported by this implementation, not merely untested.

## What this does not establish

- Not a same-B controlled comparison; the auto-sizing differs by design.
- No 64-bit run, no multi-thread, no multiple-large-factor data.
- One seed, one machine; no asymptotic claim.
