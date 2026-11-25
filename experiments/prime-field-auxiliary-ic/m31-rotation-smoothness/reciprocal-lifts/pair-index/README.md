# Contiguous index for the bound-89 M31 reciprocal census

The native pair generator enumerates 1,083,160 smooth integers, of which
541,327 are nonsquares. Its 538,627 distinct nonsquare keys occupy slots in
a table of 2,097,152 unsigned 64-bit words (16 MiB for the slots). The low
bits of a key choose the first slot. Linear probing compares the entire key.
A slot stores the nonzero key in its upper word and the insertion ordinal in
its lower word. A duplicate replaces the value at that ordinal. The separate
ordered vector therefore retains the Python census iteration order. Capacity
exceeds the total number of generated entries, so a probe always has an empty
slot available. Slot.lean proves the encoding bounds, word extraction and
reachability of an empty slot on a cyclic traversal.

The following commands run from the reciprocal-lifts directory on Apple ARM64
with clang and Python with gmpy2.

```sh
out=$(mktemp -d)
clang++ -std=c++17 -O3 -mcpu=native native-pairs/pairs.cpp -o "$out/base"
clang++ -std=c++17 -O3 -mcpu=native -DM31_RESERVE_INDEX native-pairs/pairs.cpp -o "$out/reserved"
clang++ -std=c++17 -O3 -mcpu=native -DM31_FLAT_INDEX native-pairs/pairs.cpp -o "$out/flat"
clang -O3 -mcpu=native -c ../../m31-native-product/product.c -o "$out/product.o"
clang++ -std=c++17 -O3 -mcpu=native -DM31_DIRECT_INVERSE_MASKS native-masks/masks.cpp "$out/product.o" -o "$out/direct"
python3 native-pairs/check.py "$out/base" "$out/reserved" "$out/flat"
python3 pair-index/compare.py "$out/base" "$out/reserved" "$out/flat" "$out/direct"
python3 pair-index/compare_reference.py "$out/flat" "$out/direct"
```

On one Apple M4 Pro the native panel in timings.csv used all six orders of
three paths, each with the same downstream direct mask executable. The median
paired complete-census speedup was 3.397 over the baseline std::unordered_map
and 2.073 over that map after reserving space. The independent eight-block
comparison in reference.csv alternated the original GMP census with the full
flat-index native path. Median elapsed times were 1.262 s and 0.0557 s,
respectively. Median paired speedup was 23.60 (range 17.44 to 30.48).
All paths used fresh processes on the same host, with normal OS caching.
The native path includes pair enumeration, serialization, both process
launches and the final phase counts. Each output matched phases.csv.
