# Eight-product dots on small arrays

The six processes in small-rows.csv ran on an unpinned Apple M4 Pro. Apple Clang 21.0.0 compiled the unchanged bench_eight.c with the command below for each row count. The second pass reused the binaries in reverse order. The row counts represent array lengths. The inputs are the benchmark's deterministic canonical operands and boundary cases.

```sh
for n in 17 32 71; do
    clang -std=c11 -O3 -mcpu=native -DN=$n bench_eight.c -o /tmp/dot$n
done
for n in 17 32 71 71 32 17; do /tmp/dot$n; done
```

Each process checked every output from all six kernels against the 128-bit reference. Each CSV entry is the median of 48 samples following 12 warmup rounds. Samples traverse the same small arrays repeatedly. These measurements cover warm arithmetic throughput and exclude input generation.
