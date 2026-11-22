# Specialized native IC smoothness arithmetic

The native multiplicative-group index-calculus engine now uses precomputed
fixed-divisor arithmetic and four-prime rejection blocks in its smoothness
stage. On this physical Apple ARM64 host, the exploratory median paired
thread-CPU ratios were 1.54x, 1.89x and 2.36x for uniform 32-, 48- and 64-bit
words, and 1.39x for smooth products under a 48-bit ceiling.

The production integration is in `src/indexcalc.c` and the private arithmetic
helpers are in `src/ic_trial.h`. Both collection methods and individual-log
smoothness checks use the same immutable descriptors. The public C API and
opaque context ABI remain unchanged, so existing bindings use the kernel
when rebuilt against the updated library.

## Arithmetic and scheduling

For an odd factor-base prime q, setup computes its inverse modulo 2^64 and
floor((2^64-1)/q). Multiplying a residual by the inverse modulo 2^64 gives
its exact quotient precisely when the product is at most the latter bound.
Otherwise q does not divide the residual. Successful removal reuses that
quotient, avoiding both remainder and division instructions. Prime 2 uses
count-trailing-zeros and a shift. All overflow is unsigned and intentional.

Four independent inverse products are tested together. A block is skipped
only if every prime misses and the square of the largest prime does not
exceed the residual. This preserves the original early exit for prime
residuals. Any possible hit falls through to normal exact removal. The
descriptor for 2 cannot pass the block rejection test.

Descriptor setup is outside target-dependent work and requires 16 additional
bytes per factor-base prime, shared by worker threads. The measured largest
base has 1,547 primes and uses 24,752 additional bytes. The implementation
uses ordinary C integer operations and the compiler's existing trailing-zero
builtin; no architecture-specific runtime dispatch is introduced. Physical
correctness and timing in this receipt cover Apple ARM64.

## Paired stage results

Each workload has 65,536 deterministic inputs, with nine repetitions and four
batches per sample. Reference and optimized order alternate. The reference
is the original `trial_factor` body from commit `9f47ea93e0`, frozen verbatim
apart from its function name in `reference.h`. Both versions are compiled
into the same executable with the same compiler and flags.

| Input law | Prime bound | Base primes | Median CPU ratio | CPU ratio min–max | Median wall ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uniform 32-bit words | 250 | 53 | 1.54x | 1.28–1.65x | 1.54x |
| Uniform 48-bit words | 2,000 | 303 | 1.89x | 1.58–2.27x | 1.75x |
| Uniform 64-bit words | 13,000 | 1,547 | 2.36x | 2.05–2.50x | 2.35x |
| Smooth products, 48-bit ceiling | 2,000 | 303 | 1.39x | 1.28–1.57x | 1.59x |

Ratios are reference time divided by optimized time, paired by repetition.
The timing interval covers complete smoothness calls, relation writes and
checksum accumulation. Input generation, descriptor construction and exact
output comparisons are outside it. Descriptor setup times are separate raw
fields; the local clock can round very short setup intervals to zero.

These are shared-host stage diagnostics under `docs/IC_BENCHMARK_TIERS.md`.
Active unrelated jobs produced substantial scheduling noise. No affinity,
frequency, IRQ, memory-placement or cloud-instance tier gate was established.
The promoted wall-speedup field therefore remains null. Thread CPU time
helps expose scheduling effects but does not control frequency or competing
cache traffic. The raw minimum and maximum wall ratios are in `summary.json`.
These workloads exercise the arithmetic stage, with uniform residuals and
explicit smooth-product controls; they are not natural-query yield estimates
or complete IC-versus-rho comparisons.

## Correctness and validation

- All 15 C test suites passed with `CA_WERROR=ON`.
- The index-calculus executable passed 859,153 checks under AddressSanitizer
  and UndefinedBehaviorSanitizer. Existing solves cover both collectors,
  multiple worker counts, nonprimitive bases and the prime-power LA path.
- Fixed-divisor tests compare against ordinary division for every prime up
  to 13,000 and the largest 32-bit prime, including prime powers and their
  neighbors, large exact multiples, UINT64_MAX and deterministic random words.
- The stage replay matched all 786,432 complete relation comparisons,
  including success/failure, count, columns and exponents. Each input is
  checked with an empty, nearly full and full output buffer and column
  offset 7.

`validation-tests.log` and `validation-sanitizers.log` retain the final test
outputs. `receipt.json` records the compiler, source and binary hashes,
resource observations, flags, seed and timing boundary. `samples.jsonl` and
`summary.json` retain every final timing sample and the paired statistics.
The small initial pilot and the scalar-inverse-only attempt are preserved in
`pilot-noisy.jsonl` and `scalar-inverse-noisy.jsonl`; they motivated batching.
Those earlier files have no full build receipt and remain preliminary.

Replay from the repository root:

```sh
python3 experiments/ic-native-trial-20261115/run.py
cmake --build /tmp/cryptanalysis-ic-native-20261115 -j 3
ctest --test-dir /tmp/cryptanalysis-ic-native-20261115 --output-on-failure
```

The replay updates the final receipt and sample files. Preserve an existing
run elsewhere before replaying when retaining its measurements is necessary.
Source hashes identify the actual working-tree inputs, including any local
changes; the receipt's checkout commit alone does not identify the build.
