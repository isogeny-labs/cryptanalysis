# Reciprocal lift masks for the bound-89 M31 census

The native process consumes the ordered representatives from native-pairs. It
builds five 31-bit masks for each reciprocal orbit pair, including both signs
of the curve constant. The two coordinates share the auxiliary mask by
Transport.lean. Thirty batched squarings classify every cubic value using the
predicate proved in ../SquareTest.lean.
Each output phase counts the intersection of a left mask with the rotated
right mask using popcount.

Both native arms use the same field product kernel, mask packing and phase
counter. Direct computes one inverse per representative and rotates the two
coordinates in opposite directions. Shared multiplies the inverse-coordinate
cubic by the square x^4. Its terms are then x, 2x^3 and ±14x^4. It rotates
those terms directly. InverseLift.lean proves lift equivalence over any field
at every nonzero x, including cubic zeros.

Run from reciprocal-lifts on the Apple ARM64 host with Python and gmpy2:

```sh
out=$(mktemp -d)
clang++ -std=c++17 -O3 -mcpu=native native-pairs/pairs.cpp -o "$out/pairs"
clang -O3 -mcpu=native -c ../../m31-native-product/product.c -o "$out/product.o"
clang++ -std=c++17 -O3 -mcpu=native native-masks/masks.cpp "$out/product.o" -o "$out/shared"
clang++ -std=c++17 -O3 -mcpu=native -DM31_DIRECT_INVERSE_MASKS native-masks/masks.cpp "$out/product.o" -o "$out/direct"
python3 native-masks/compare.py "$out/pairs" "$out/direct" "$out/shared"
python3 native-masks/compare_stage.py "$out/pairs" "$out/direct" "$out/shared"
```

On the M4 Pro, the six blocks in timings.csv cover each ordering of three
arms. All include a fresh pair-generator process. The Python/GMP arm includes
its Python startup. The two native arms include launching the mask process
and passing it the enumerated coordinates. Median whole-census wall seconds
were 0.509 (Python/GMP), 0.203 (direct) and 0.227 (shared). Median paired
speedups over Python/GMP were 2.38 and 2.22. Across a separate 24 paired
mask-process replays, median direct/shared time was 1.003 and shared won
13 times. There is no resolved speed advantage for the quartic substitution.

The checker independently evaluates both orbit directions in Python with
Euler's criterion and compares every mask for every selected representative
before timing. All timed outputs must match phases.csv byte for byte.
