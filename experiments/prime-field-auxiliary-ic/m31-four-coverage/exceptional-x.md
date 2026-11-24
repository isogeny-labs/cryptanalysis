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

## Interleaved square roots

Pass a third argument `interleaved` to the panel executable to compare 1, 2, 4 and 8 independent four-lane root chains. Each SIMD vector undergoes the same 29 squarings. Each path uses binary search and stages labels in groups of four. The fixed panels of 8224 coordinates divide evenly into 32-input blocks. Timings cover the entire mixed-input traversal.

Across eight shuffles per panel (314101–314108), with eight warmups and 24 measured rounds per arm, the median of the shuffle medians was:

| Input seed | 1 chain | 2 chains | 4 chains | 8 chains |
|---|---:|---:|---:|---:|
| 312001 | 81.52 | 71.70 | 66.16 | 63.85 |
| 312002 | 80.92 | 71.31 | 65.50 | 63.29 |

Values are ns/input on Apple M4 Pro. All four arms checked the saved status and ordered labels after every traversal. Raw records are in `interleaved-roots.csv`.

## Label grouping after interleaved roots

Use the third argument `grouped` for eight root chains and label groups of 4, 8, 16 and 32 inputs. The four-input control classifies the accepted lanes of each vector before moving on. The 32-input arm collects accepted lanes across eight vectors and scatters labels to the saved input offsets. Every traversal starts with deliberately incorrect output words before the timer starts.

The original local comparison on an M4 Pro is recorded in `grouped-labels.csv`. Across eight shuffles per panel, increasing the group from 4 to 32 reduced the median paired time by 2.86% and 3.25% on the saved panels and by 3.30% and 3.68% on fresh panels 315201 and 315202. Run `grouped-label-oracle.py` in a scratch directory to regenerate the two fresh input files using Python affine arithmetic. Pass either file and a shuffle from 315201 through 315208 to the executable. The saved panels used shuffles 315101 through 315108. The published harness shares one template across group sizes and was replayed for correctness; the CSV records timings from the original separate control and candidate functions.
