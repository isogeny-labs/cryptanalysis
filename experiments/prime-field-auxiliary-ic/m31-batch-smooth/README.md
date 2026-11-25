# Batch smoothness filter at M31

The local arm64 experiment compared the scalar filter with batches of 4, 8 and 16
on the 32,768 public depth-15 roots. Each of the 24 possible execution orders
appeared twice. In paired.csv, columns are wall nanoseconds per filter call.
The 16-coordinate prototype retained all 392 signed-211-smooth coordinates in
reference order. setup.csv records 64 alternating pairs of complete public
basis preparations after four warmups. The two paths differed only in the
filter library. Each call returned the same 195 ordered points.

Build the measured source with
`c++ -O3 -std=c++17 -shared -fPIC b16.cpp -o /tmp/m31-batch.so`.
Supply the resulting library as the filter argument to the neighboring
m31-packed-fiber replay. Inputs are canonical unsigned field coordinates.
The theorem in Batch.lean establishes the loop-order transformation and stable
selection for a lane-local update. The correspondence between compiled mask
operations and that update is tested empirically.

## Full-word mask comparison

On the frozen depth-15 workload, widths-filter.csv and widths-setup.csv
record 100 alternating pairs after four warmups, in wall nanoseconds.
Changing the width from 16 to 32 gave a median paired filter speedup
of 1.394× and a median paired public-basis preparation speedup of 1.172×.
Both paths returned identical ordered outputs on every timed call.

Build and replay the independent domain check with
`c++ -O3 -std=c++17 exhaustive.cpp b32.cpp -o /tmp/m31-exhaustive32 && /tmp/m31-exhaustive32`.
Local arm64 replay compared 2,147,483,647 coordinates in 32,776 blocks,
cycling through all 32 possible tail lengths. It accepted 22,819,080
coordinates in exact agreement with independent smooth-product enumeration.
Batch.lean verifies the full-word mask operations. Timings cover basis
preparation after library loading.

## Independent prime masks

independent.cpp forms each prime's divisibility mask from a saved copy of
the odd lane values and applies exact division to the current residuals.
The fresh_prime_mask theorem in the adjacent m31-native-smooth-filter/Strip.lean
proves that removing powers of earlier distinct primes preserves this test.

Build with the same flags as b32.cpp. Link independent.cpp with exhaustive.cpp
to replay the domain check. The local arm64 build matched independent
smooth-product enumeration on all 2,147,483,647 canonical coordinates,
including the order of all 22,819,080 accepted entries across 32,776 blocks.
The adjacent independent-filter.csv and independent-setup.csv give wall
nanoseconds for 100 alternating pairs after four warmups, comparing b32.cpp
with independent.cpp. The median paired speedups were 1.452× for filtering
and 1.086× for complete depth-15 public basis preparation.
