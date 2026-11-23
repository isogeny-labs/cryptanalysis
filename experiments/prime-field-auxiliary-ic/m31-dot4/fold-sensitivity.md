# Eight-product working-set and compiler comparison

The two passes in fold-sensitivity.csv ran on an Apple M4 Pro with Apple Clang 21.0.0. Each process ran all five kernels against the same generated canonical rows and checked all outputs against the 128-bit reference. The precentered kernel reads separately prepared inputs. Each timing sample computes 1,048,576 dots across repeated traversals of N rows. A single canonical traversal reads two eight-element uint32 vectors and writes one uint32 output per row, totaling 68 bytes per row. This footprint excludes the other arms' arrays.

Use the following command for each N in 2048, 65536 and 1048576, adding both -fno-vectorize and -fno-slp-vectorize for the disabled build.

```sh
clang -std=c11 -O3 -mcpu=native -DN=2048 bench_eight.c -o /tmp/dot8 && /tmp/dot8
```

Process order is recorded in the CSV. The second pass reversed the first pass and reused the same binaries. Each cell is the median of 40 measured samples after 10 warmups. Within each process, arm positions rotate and traversal order alternates every five rounds. The host was unpinned. The experiment recorded no hardware cache counters.

With vectorizers enabled, disassembly for each N contains UMULL.2D and UMLAL.2D in the deferred-fold loop. The carry-correction loop instead uses scalar widening arithmetic. Disabling both vectorizers removes the vector widening multiplies from the deferred-fold loop. The close and inconsistent ratios at 65,536 rows preclude a uniform speedup claim over the measured sizes.
