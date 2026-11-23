# Full-field square bitmap against direct M31 labels

Each process constructs the 256 MiB square-residue table, then compares it with 30 repeated M31 squarings using ARM NEON high multiplies. Both arms compute the cubic right-hand side from the same coordinate and emit a uint32 label. Setup is timed once per fresh process, including allocation and populating the table. The direct arm needs no equivalent setup. Input generation and the output comparison are outside both timed regions.

On the Apple M4 Pro with Apple Clang 21, compile bitmap_panel.c with -O3 -mcpu=native -std=c11. Run processes with seeds 1, 2 and 3. Each process advances a full-period 31-bit recurrence, skipping the noncanonical word. Each of its 12 blocks has 1048576 new coordinates. The arms alternate order and compare every label in each block. The shared host was unpinned. Process seeds identify starting points on the same recurrence; independence between processes is not assumed.

The direct arm won 34 of 36 paired blocks and had the lower process median in all three processes even with bitmap setup excluded. The median per-query cost model therefore has no positive lookup-count break-even in this workload. The measurement concerns streamed coordinate labels. Different access locality, smaller tables, requests for actual roots, and full collector workloads require separate evidence.

BitmapCoverage.lean proves that enumerating through floor(n/2) covers all squares modulo n for every nonzero modulus. This certifies the mathematical coverage of the bitmap construction. The C implementation was checked against direct squaring on every measured coordinate.

## Signed and canonical reductions on streamed coordinates

Run the same binary with a seed and the extra argument folds. Seeds 41, 42 and 43 each supply 24 new blocks. Each block compares three direct modes with identical inputs, vector batch size, cubic evaluation and output layout. Arm 0 is the original canonical comparison, arm 1 selects the smaller unsigned word after a possible subtraction, and arm 2 uses the signed reduction from ../m31-balanced-square/census.inc. Arm 2 includes its final canonicalization. All six arm orders occur four times per process. The bitmap supplies an untimed reference before each block; every arm's output is checked after timing. fold_stream.csv retains the 216 measurements. Apple Clang 21 on the unpinned M4 Pro emitted separate specialized loops for all three modes.

The per-block ratio divides the lower of the two canonical times by the signed time. Median ratios were 1.154, 1.155 and 1.141 in process order. The signed arm beat both canonical arms on 16, 19 and 14 of 24 blocks. In process 43 the unsigned-minimum arm had a lower standalone median than the signed arm. The paired statistic uses the matched timings on each block; independently taking medians of each arm can yield a different ordering. The results measure throughput of lift labels on streamed inputs.
