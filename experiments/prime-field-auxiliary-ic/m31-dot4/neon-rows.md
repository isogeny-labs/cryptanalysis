# Eight-product NEON row comparison

Six fresh processes ran on an unpinned Apple M4 Pro using Apple Clang 21.0.0. Build bench_eight.c with -O3 -mcpu=native and -DN set to 2048, 65535, or 1048576. The second pass reused the executables in reverse order. The odd-sized input exercises the single-row tail. No input conversion or packing is needed for the new kernel. The canonical inputs and uint32 outputs use 68 bytes per row.

Each process first compared every row in each of six arms with a uint128 reference. It then rotated arm positions, reversing traversal order every six rounds. The CSV stores each arm's median nanoseconds per dot after 12 warmups and 48 measured samples. Every sample traversed the entire row array enough times to compute at least 1048576 dots. Run-to-run variation on this shared host is visible in the controls. Timings describe repeated array throughput.

The ARM64 assembly for neon_rows uses paired contiguous vector loads, widening vector multiply-adds, and pairwise addition across lanes. The neon_lane_fold theorem covers lane bounds, folding, narrowing and the canonical remainder for arbitrary canonical products. Compiler and instruction semantics are outside its scope.
