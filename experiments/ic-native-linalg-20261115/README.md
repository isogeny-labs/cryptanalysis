# Native IC rational reconstruction and graph elimination

Signed rational reconstruction reduces single-target online work in the
native multiplicative-group IC engine. On this physical Apple ARM64 host,
the fresh five-point exploratory panel measured median online CPU ratios
of 16.32x for the 48-bit case and 28.53x for the 54-bit prime-power case.
Median trial-residue counts fell by 20.01x and 22.75x respectively. Exact
forest elimination and specialized modular arithmetic also reduced setup
CPU time by 4.60x and 4.44x in those cases.

All 5,000 scalar answers in the paired panel were independently replayed.
Every case contains five distinct public points, and each point is solved
100 times independently with the same reusable setup. The reported ratio
for a point compares the arithmetic means of its 100 separately recorded
online intervals. The headline median is over the five paired point ratios.
This is repeated solving of one point per measurement cell, with no
target-dependent cache or cross-target log table. Every raw interval and
failed/noisy observation remains in the artifacts.

These are **exploratory shared-host implementation measurements**. The
Tier 0/1 environment gate in `docs/IC_BENCHMARK_TIERS.md` was not established;
the promoted wall-speedup field remains null. No IC-versus-rho result is
inferred from this comparison against the previous native IC implementation.

## Primary online results

| Modulus p | Method | Base primes | Median CPU ratio | CPU ratio over five points | Median trial-residue ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| 2,000,000,579 | Linear sieve | 48 | 6.05x | 2.98–7.09x | 12.01x |
| 1,099,511,627,791 | Linear sieve | 143 | 9.57x | 8.98–11.02x | 14.55x |
| 281,474,976,710,597 | Linear sieve | 303 | 16.32x | 8.44–20.94x | 20.01x |
| 14,636,773,816,760,213 | Linear sieve, prime-power LA | 565 | 28.53x | 23.21–35.94x | 22.75x |
| 2,000,000,579 | Random exponent | 68 | 4.63x | 2.36–5.89x | 10.70x |

Ratios are reference time/count divided by candidate time/count. The
prime-power case uses p-1 = 52 * 16,777,259^2 and exercises Hensel lifting.
The native auto-parameter policy, seed 12345, one collector thread, generator,
public point and resource cap are fixed between arms. The 54-bit case's five
reference means ranged from 118.94 to 212.08 microseconds per online solve;
candidate means ranged from 5.06 to 6.10 microseconds.

Local timers have microsecond-scale granularity, and unrelated host jobs
were active. The smallest cells are sensitive to timer overhead and host
noise. The per-point 100-repeat records improve observation of the small
intervals, while preserving each individual solve and its answer. They do
not substitute for an isolated-host replication or justify a universal ratio.

Fixture indices 5 through 9 were frozen before the final panel. Target
construction and primitive-root fixture generation precede timing. The
online clock surrounds each `ca_ic_log` call, including its internal scalar
replay. An additional independent `ca_powmod(g,x,p)==h` check runs afterward
and has its own recorded duration. Setup includes the entire
`ca_ic_precompute` call: table construction, collection, LA and factor-log
verification. Source/build hashes, executable hashes and timer boundaries
are in `receipt.json`.

## Algorithm and arithmetic changes

The original individual-log search factors v = h*zeta^e as a single integer
below p. The new search runs the Euclidean recurrence until a remainder a
is at most floor(sqrt(p)). The accompanying signed coefficient b satisfies
a=b*v modulo p and has magnitude at most p/(floor(sqrt(p))+1). If a and |b|
are smooth over the verified factor base, their logs give

```
log_zeta(h) = log_zeta(a) - log_zeta(|b|) - log_zeta(sign(b)) - e  (mod p-1).
```

The sign term is 0 or (p-1)/2. The final exponentiation verifies the answer
before returning it. Both factorizations, failed candidates, reconstruction,
random-walk work and the internal replay are included in online timing.
The trial-residue count records walk candidates; each candidate can require
two smoothness tests, with the denominator test skipped when the numerator
fails. That count is distinct from the number of trial-factor calls.

The walk also uses a reusable 4,096-entry Montgomery power table (32 KiB)
instead of exponentiating the selected short step every iteration. The
step distribution and random-generator consumption remain unchanged.

For the linear sieve, a relation contains h_u+h_v or 2*h_u in its auxiliary
columns. A breadth-first spanning forest expresses each auxiliary log as
an affine function of one component root and the factor-base logs. Exact
substitution removes the forest equations. Component roots remain in the
reduced system, including coefficient 2 for odd cycles and self-loops, so
the transformation needs no division by 2.

| Case | Original columns | Reduced rows x columns | Reduced entries | Lanczos iterations, reference to candidate | Median setup CPU ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| 31-bit linear sieve | 323 | 282 x 49 | 4,660 | 230 to 49 | 2.63x |
| 41-bit linear sieve | 1,094 | 638 x 144 | 13,386 | 543 to 144 | 6.66x |
| 48-bit linear sieve | 2,504 | 1,324 x 304 | 30,537 | 1,162 to 304 | 4.60x |
| 54-bit prime-power case | 5,166 | 2,526 x 566 | 61,138 | 2,241 to 566 | 4.44x |

The expression workspace is capped at 64 MiB. Unsupported row patterns,
coefficient-range failures or allocation failures fall back to the existing
matrix builder. The largest panel case uses about 10.4 MB for expressions.
The random-exponent collector keeps its original matrix construction.

The modular solver keeps vectors and matrix entries in ordinary residues
and converts reused scalar multipliers to Montgomery form. Dot products
use a modulus-dependent, overflow-safe accumulation interval. Sparse sums
use a one-word kernel only when the total absolute coefficient weight proves
that all row and column sums fit; otherwise the 128-bit kernel remains.
Dense elimination normalizes inputs once and uses the same mixed-domain
products. The modulus-2 dense path is retained.

## Verification and proof scope

- All 15 C suites passed with compiler warnings treated as errors.
- The linalg and indexcalc suites passed AddressSanitizer and
  UndefinedBehaviorSanitizer, including full-width prime-modulus tests.
- All 5,000 final paired-panel answers passed independent exponentiation;
  collection counts, base sizes, public inputs and verified factor logs agree.
- The graph harness exhaustively compares projected solution sets in 96
  cases over moduli 3 through 6, including disconnected graphs, self-loops,
  even cycles, odd cycles, inconsistent variants and absent auxiliary edges.
- 700,000 independent reconstruction checks verify the exact modular
  identity, positive numerator/denominator magnitudes and both size bounds,
  up to the largest 64-bit prime. Both auxiliary harnesses also pass sanitizers.
- Five Lean lemmas check Euclidean congruence preservation, tree and cycle
  substitutions, and rational-log extraction. See `PROOF_MAP.md` for exact
  hypotheses, dependency pins and the remaining program-level obligations.

Rational reconstruction and forest elimination use established techniques.
The contribution here is their specialized integration and measured work
reduction in this native implementation. The checked Lean lemmas cover
local algebraic invariants; full C verification and graph/loop invariants
remain separate obligations.

## Artifacts and replay

`reference_indexcalc.c` and `reference_linalg.c` freeze commit
`888727f277b3ad4926c8d057e575887fd6c8e27d`. The reference objects are linked
ahead of the same library used by the candidate, so both executables share
the other implementation sources, compiler and flags. The reference already
includes the preceding four-prime smoothness optimization.

`before-rational-*` preserves the earlier phase, which improved setup while
showing weak or negative online changes. `graph_candidate.h` preserves the
initial graph helper prototype; the production helper is in `src/indexcalc.c`.
`samples.jsonl` preserves all final arms and individual online runs;
`summary.json` preserves every paired ratio. Validation and formal logs are
stored alongside them. The public header's algorithm-description comment
was updated after measurement; executable source behavior is unchanged.

From the repository root:

```sh
cmake -S . -B /tmp/cryptanalysis-ic-native-20261115 -DCA_CUPQC=OFF -DCA_WERROR=ON -DCA_BUILD_SHARED=OFF -DCA_BUILD_TOOLS=OFF
python3 experiments/ic-native-linalg-20261115/run.py
cmake --build /tmp/cryptanalysis-ic-native-20261115 -j 3
ctest --test-dir /tmp/cryptanalysis-ic-native-20261115 --output-on-failure
cc -O3 -std=c11 -Iinclude -Isrc experiments/ic-native-linalg-20261115/graph_test.c /tmp/cryptanalysis-ic-native-20261115/libcryptanalysis.a -lm -lpthread -o /tmp/ic-graph-test
/tmp/ic-graph-test
```

Replay overwrites final measurement files; copy the existing run first when
retaining its receipts. The next promotion step is the frozen panel on a
controlled allocation with resource/noise receipts and a physical x86-64
rebuild, alongside the measured ARM64 implementation.
