# Full-field square bitmap against direct M31 labels

Each process constructs the 256 MiB square-residue table, then compares it with 30 repeated M31 squarings using ARM NEON high multiplies. Both arms compute the cubic right-hand side from the same coordinate and emit a uint32 label. Setup is timed once per fresh process, including allocation and populating the table. The direct arm needs no equivalent setup. Input generation and the output comparison are outside both timed regions.

On the Apple M4 Pro with Apple Clang 21, compile bitmap_panel.c with -O3 -mcpu=native -std=c11. Run processes with seeds 1, 2 and 3. Each process advances a full-period 31-bit recurrence, skipping the noncanonical word. Each of its 12 blocks has 1048576 new coordinates. The arms alternate order and compare every label in each block. The shared host was unpinned. Process seeds identify starting points on the same recurrence; independence between processes is not assumed.

The direct arm won 34 of 36 paired blocks and had the lower process median in all three processes even with bitmap setup excluded. The median per-query cost model therefore has no positive lookup-count break-even in this workload. The measurement concerns streamed coordinate labels. Different access locality, smaller tables, requests for actual roots, and full collector workloads require separate evidence.

BitmapCoverage.lean proves that enumerating through floor(n/2) covers all squares modulo n for every nonzero modulus. This certifies the mathematical coverage of the bitmap construction. The C implementation was checked against direct squaring on every measured coordinate.
