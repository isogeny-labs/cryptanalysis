# Exceptional M31 orbit starts

The hash folds x with x shifted right by four bits and uses the low byte as an index into 256 words. The table stores the full coordinate for each of 32 exceptional starts. ExceptionalX.lean proves exact membership in this specified list for every canonical input. The proof uses native_decide for the finite table certificates. The identification of the list with short orbits on the curve is outside the theorem.

On an Apple M4 Pro, each input panel comprised 8192 random x values and 32 exceptional starts. For each of eight shuffles we rotated three implementations, discarded six warmup rounds and retained 18 traversals per implementation. Every traversal compared all statuses and ordered labels against the saved oracle rows. The table reports the median of the eight traversal medians in nanoseconds per input.

| Input seed | Scalar roots and inline labels | SIMD roots and staged labels, binary search | Same SIMD path, hashed lookup |
|---|---:|---:|---:|
| 312001 | 103.69 | 82.56 | 82.48 |
| 312002 | 103.26 | 82.43 | 81.96 |

Hashing alone had a small and inconsistent timing effect. Both SIMD paths compute the lift, check the exceptional starts and produce labels for the accepted full orbits. Setup of fixed offsets is outside the timed traversal.

To replay from this directory on native Apple silicon, substitute either saved panel seed and any shuffle from 312101 through 312108.

```sh
gzip -dc exceptional-x-312001.txt.gz > /tmp/m31-exceptional-panel.txt
clang++ -std=c++20 -O3 -mcpu=native -DM31_REGISTER_BIC exceptional-x-panel.cpp -o /tmp/m31-exceptional-panel
/tmp/m31-exceptional-panel /tmp/m31-exceptional-panel.txt 312101
clang++ -std=c++20 -O3 exceptional-x-check.cpp -o /tmp/m31-exceptional-check
/tmp/m31-exceptional-check
```

The last command compares the compiled hash against a sorted traversal for every field input, then checks the sentinel and the maximum unsigned word.
