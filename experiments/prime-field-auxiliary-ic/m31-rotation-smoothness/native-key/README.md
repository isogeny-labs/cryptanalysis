# M31 reciprocal orbit census

Enumerate each odd smooth positive integer below the modulus once, using nondecreasing prime factors. Keep the nonsquares. Each output is the complete sorted set of oriented reciprocal keys, together with the count of distinct two-element reciprocal pairs. The common parity recurrence charges one Euler character evaluation per prime. A reciprocal key fixed by inversion contributes zero two-element pairs.

## Frozen local comparison

Compile bench.cpp using clang++ -std=c++17 -O3 -mcpu=native. Run once, single threaded, on the local ARM64 CPU. At each bound (47 and 67) construct one untimed direct reference. Time twelve rounds in two cycles through all six arm orders. Compare the entire output to the reference after every timed call. Timing covers prime setup, enumeration, encoding, sort, deduplication and pair counting. Output comparison and destruction of the returned vector occur after timing. Retain every row. Summarize each arm by median wall time and comparisons by the median of within-round ratios.

Direct computes the forward key for each emitted integer and batch-inverts the keys. Batch carries the forward key through the enumeration and uses the same batch inversion. Carry tracks both keys and eliminates the prefix array. These are warm-process, unisolated component measurements.
