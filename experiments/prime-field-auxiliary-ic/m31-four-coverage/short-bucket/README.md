# Exact lookup for 31-bit integer keys

The experiment constructs indexes from 28,033 existing synthetic keys and probes 673,130 inputs per traversal. Each seed uses eight planted hits and otherwise uniform 31-bit queries. Round -1 checks every table key and the endpoints 0 and 2147483647. Six timed rounds follow with randomized arm order. Construction and lookup columns are separate wall times in nanoseconds. CSV fields are seed, round, arm, build_ns, probe_ns.

The screen uses eight datasets starting at seed 319201. Arm 0 uses binary search within a 12-bit prefix and 32-bit offsets. Arms 1 and 2 use the same prefix and 16-bit offsets for binary and linear search respectively. Arms 3 through 6 use 16-bit offsets and four-key NEON comparisons with prefix widths 12, 14, 15 and 16 respectively. Arm 5 minimized the median per-seed build-plus-probe time. The confirmation compares arms 0 and 5 on eight separate datasets starting at seed 319301.

On Apple M4 Pro, the confirmation medians were 5.67 ms for arm 0 and 1.08 ms for arm 5, including index construction. Synthetic keys, inputs and expected results were prepared before timing. The optimal width can vary with table size and key distribution.

Reproduce on native Apple silicon from this directory.

```sh
clang++ -std=c++20 -O3 -mcpu=native bench.cpp -o /tmp/m31-prefix-replay
/tmp/m31-prefix-replay 319201 > /tmp/m31-prefix-screen.csv
winner=$(python3 summary.py /tmp/m31-prefix-screen.csv)
/tmp/m31-prefix-replay 319301 "$winner" > /tmp/m31-prefix-confirm.csv
python3 summary.py /tmp/m31-prefix-confirm.csv
```

PaddedScan.lean proves the scan length recurrence, bounds each load within the array extended by four words, and proves membership equivalence for the 15-bit prefix under the stated offset and padding hypotheses. The benchmark compares each output byte with an independent reference set.
