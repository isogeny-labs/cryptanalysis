# Cost at the first compatible level-two smoothness bound

This comparison changes the largest allowed prime from 89 to 211. Both
executables carry the two orbit keys during enumeration, use the contiguous
index, and compute the direct inverse-coordinate masks. Each complete run
starts fresh pair and mask processes and includes the transfer of the selected
coordinates and collection of all 31 output rows.

On the shared Apple M4 Pro with Apple clang 21.0.0, eight alternating paired
blocks gave median complete wall times of 0.0783 s and 0.5373 s at bounds 89
and 211. Median within-block cost ratio was 7.27 (range 2.56 to 12.44).
Median total child CPU times were 0.0456 s and 0.4045 s; median paired CPU
cost ratio was 8.95. Host contention varied during the panel. Read timings.csv
for each observation, including the pair-generation phase. These times use one
host and describe the public census only.

The larger census emits 104,580 distinct reciprocal orbit pairs, up from
3,302, or 31.67 times as many. An independent depth-first enumeration computes
each quadratic character and forward key by modular powering, sorts and
deduplicates keys, and tests for inverses by binary search. Its complete
ordered list of smaller keys matched. An independent Python/GMP oracle
recomputed every lift mask in both directions and accumulated the phase
counts. Both the native cross-check and every timed run matched phases.csv.

For the pinned depth-five fiber, coverage.json records every distinct sibling
pair attained under compatible rescaling, up to the 31 rotations. The bound
increase changes that count from zero to one among 31 sibling pairs across
five levels. It is the previously certified level-two pair at scale 16384.
Total reciprocal orbit yield and coverage of this particular fiber are
different quantities.

Replay from the parent reciprocal-lifts directory using Python with gmpy2:

```sh
out=$(mktemp -d)
clang -O3 -mcpu=native -c ../../m31-native-product/product.c -o "$out/product.o"
clang++ -std=c++17 -O3 -mcpu=native bound-211/keys.cpp -o "$out/keys"
for n in 89 211; do
    flag=""
    if [ "$n" = 211 ]; then flag=-DM31_BOUND_211; fi
    clang++ -std=c++17 -O3 -mcpu=native -DM31_FLAT_INDEX $flag native-pairs/pairs.cpp -o "$out/pairs$n"
    clang++ -std=c++17 -O3 -mcpu=native -DM31_DIRECT_INVERSE_MASKS $flag native-masks/masks.cpp "$out/product.o" -o "$out/masks$n"
done
python3 bound-211/reference.py "$out/pairs211" "$out/keys" > "$out/verified.csv"
cmp "$out/verified.csv" bound-211/phases.csv
python3 bound-211/coverage.py "$out/pairs89" "$out/pairs211" > "$out/coverage.json"
cmp "$out/coverage.json" bound-211/coverage.json
python3 bound-211/time_panel.py "$out"
```
