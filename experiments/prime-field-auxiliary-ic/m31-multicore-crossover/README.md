# Multicore CPU and Metal M31 inversion on a shared M4 Pro

A CPU comparison with ten scheduled tasks changed materially between consecutive panels. At 1,048,576 words the median paired CPU/GPU wall-time ratio was 2.02 [1.38, 3.20] in the first and 1.12 [0.66, 2.48] in the second. GPU wall time won 16 of 20 pairs and then 10 of 20. At 524,288 words the direction reversed, from 1.49 [1.02, 1.90] to 0.60 [0.55, 0.83]. These descriptive 95% block-bootstrap intervals are computed separately. This evidence does not support a stable crossover on the shared host.

The large-array GPU command-buffer device-time median stayed at about 177 μs in both panels. Corresponding synchronous wall medians moved from 1.138 to 2.944 ms. The second panel began with a one-minute system load average of 60.73 and ended at 104.07, on a host with 14 physical cores. The discrepancy identifies time outside the reported GPU interval as the main source of this between-panel latency change. This instrumentation cannot assign the difference to a specific queue or scheduler event.

The CPU implementation and GPU shader are the existing M31 field FFI and eight-word Metal kernel. The CPU modes use a direct call or 4, 10 and 14 tasks in dispatch_apply on the user-initiated global queue. Tasks process disjoint whole tiles where possible. The OS schedules tasks across ten performance and four efficiency cores. An assigned task count is not a measurement of simultaneous core occupancy. Empty CPU partitions are included for the smallest inputs.

Each panel rotates ten array sizes and balances all five method positions and directed adjacencies in 20 rounds. Fresh identical inputs per paired round and size include edge residues. The driver checks every result by modular multiplication. Shared buffers and pipelines are allocated before the timed rounds. The CPU timer includes task submission and joining for parallel modes. GPU wall time includes command encoding, submission and waiting. Validation is outside the clocks. The second panel repeats the same seed and workload.

Build and replay from this directory on macOS:

```sh
clang++ -O3 -std=c++17 -fobjc-arc panel.mm ../m31-field-ffi/m31.cpp \
  -framework Foundation -framework Metal -o panel
./panel
python3 analyze.py rows.csv
python3 analyze.py repeat.csv
```

The shader is loaded from the sibling m31-metal-inverse directory. Columns are round, word count, method (0 direct CPU, 1/2/3 parallel CPU with 4/10/14 tasks, 4 Metal batch), wall seconds, and Metal device seconds. The first run produced rows.csv and the second produced repeat.csv. These are standalone inversion timings.
