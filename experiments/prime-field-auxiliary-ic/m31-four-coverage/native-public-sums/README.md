# Native M31 public sum census

The 17 input points are the factor_base entries from the public field31_s5_base0 fixture at commit 9a1d8a6cf. Each emitted coordinate represents an exact weight-four signed sum, with the first nonzero coefficient positive. Increasing basis indices avoid permutations. The magnitude of each coefficient may be 1 through 4. Only abscissae are emitted.

The benchmark constructs the needed multiples, generates the intermediate sums and emits the full set in memory. For widths above one it takes one field inverse per nonempty batch of affine denominators. A zero product aborts the run. This specialized ordinary-chord enumeration was validated on the supplied fixture.

On an Apple M4 Pro, 18 shuffled rounds with a fresh process per arm produced median generation times of 3.129 ms, 0.425 ms and 0.343 ms for widths 1, 32 and 128. Each output was subsequently sorted, checked for duplicates and compared by digest. The timings omit process launch, parsing the input points, verification, output serialization, and any downstream indexing. The raw CSV columns are round, width, and milliseconds.

Replay on a little-endian machine from this directory:

```sh
clang++ -std=c++20 -O3 -mcpu=native census.cpp -o /tmp/m31-public-census
/tmp/m31-public-census 128 /tmp/m31-public-x.bin < basis.txt
shasum -a 256 /tmp/m31-public-x.bin
```

The expected SHA-256 for the 28,033 sorted little-endian uint32 words is `94ea695bcce35285ed2dea298caeebc4c401fcf6c41931a65cba1700b3b2c0fb`. Independent PARI/GP and Python affine enumerations produced this digest. The corresponding finite-support proof is in the parent directory's ArchiveRepeatedSums.lean.

## Sorted public table timing

Pass a fourth command-line word to select the sort and print two comma-separated milliseconds measurements. The first ends after generation. The second covers generation through completion of the in-memory sort, including radix scratch allocation and release. Input parsing, duplicate checks, serialization and downstream lookups fall outside both measurements.

```sh
/tmp/m31-public-census paired-512 /tmp/m31-public-x.bin radix < basis.txt
```

The local Apple M4 Pro comparison in `sorted-table-times.csv` uses the same binary for all four combinations of generator (`1024` or `paired-512`) and sort (`std` or `radix`). Each of the 24 possible execution orders occurs once, with one fresh process per arm and the expected SHA-256 verified after each run. The radix sort makes three stable passes with 11, 11 and 10 significant bits. Its scratch storage includes a second key array and 2,048 counters.
