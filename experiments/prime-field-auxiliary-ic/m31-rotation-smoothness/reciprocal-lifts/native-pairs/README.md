# Bound-89 reciprocal pair generation

The native helper follows the existing prime-by-prime smooth enumeration. Along
each edge it multiplies the forward and inverse 31st-power keys by precomputed
prime-specific factors. The map retains first insertion order and last value.
It emits only representatives on the smaller-key side of a two-element pair.
The existing Python census consumes that list and evaluates all curve and twist
lift masks and all 31 phase counts. SignedProduct.lean in the parent directory
proves the sign recurrence. OrbitKeys.lean proves the two key updates on units.

Build and run from the parent directory on ARM64 macOS with clang and a Python
environment containing gmpy2.

```sh
out=$(mktemp -d)
clang++ -std=c++17 -O3 -mcpu=native native-pairs/pairs.cpp -o "$out/carry"
clang++ -std=c++17 -O3 -mcpu=native -DM31_RECOMPUTE_KEYS native-pairs/pairs.cpp -o "$out/recompute"
python3 native-pairs/check.py "$out/carry" "$out/recompute"
python3 census.py --gmp --pair-generator "$out/carry"
python3 native-pairs/compare.py "$out/carry" "$out/recompute" > "$out/timings.csv"
```

On an Apple M4 Pro, the six blocks in timings.csv cover each order of three
arms once. Every timed command launches a fresh process and reproduces phases.csv
byte for byte. The reference uses the existing Python enumeration and GMP
inversion. Both C++ arms use the same traversal, grouping, helper interface
and Python/GMP lift calculation. Recompute evaluates key and inverse powers
for each emitted nonsquare before grouping. Carry replaces those powers with
the multiplicative recurrence during traversal. Neither native arm changes
the factor bound or lift predicates.

Median whole-census wall seconds were 1.034 (reference), 0.441 (recompute)
and 0.342 (carry). Median within-block ratios were 3.016 for reference/carry
and 1.288 for recompute/carry. The preliminary two-arm comparison is preserved
in initial-paired.csv. Both helpers also matched all 538,627 ordered Python
map entries and all 3,302 selected representatives. These timings cover the
finite public-coordinate census through CSV emission.
