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

## Mersenne reduction in the sorted table build

The default field multiplication adds the low 31 bits of a 64-bit product to the high bits and conditionally subtracts the modulus. The chord formula also folds the slope square and the two x-coordinate subtractions together. The input coordinates must be canonical field elements. The product and accumulator bounds and the resulting abscissa identity are proved in the parent directory's `WordReduction.lean`.

Compile `census.cpp` with `-DM31_BASELINE_REMAINDER` for the original remainder and separate chord subtractions, or `-DM31_SEPARATE_CHORD` to use the Mersenne product fold alone. In `reduction-times.csv`, `remainder` denotes the original control, `fold` uses the product fold alone, and `fused` denotes the default. The comparison uses paired-512 generation, radix sort and multiset output. Each fixture runs every permutation of the three arms six times, in fresh processes. The fixtures and round order are interleaved, and every sorted output is checked against the fixture's independent digest.

## Interleaved batch products

The `paired-512-lanes4` arm distributes each batch's denominators over four running products. A two-level multiplication tree obtains all four reciprocals with one field inversion, including for partial batches. The reverse pass visits requests in the original order. The `paired-512` arm uses one running product. Both arms have the same ordinary-chord precondition.

```sh
/tmp/m31-public-census paired-512-lanes4 /tmp/m31-public-x.bin radix < basis.txt
```

In `lane-times.csv`, the frozen binary is built from commit `529249a9a`. The current binary contains both lane counts. Each fixture uses 36 fresh-process rounds, with each of the six arm orders repeated six times and the fixture rounds shuffled together. Generation and sorted-table times are in milliseconds. Each output was checked against its independent fixture digest. The algebra for partitioning products and reversing the tree is in the parent directory's `PairInversion.lean`.

## Exact multiplicity lookup

`prefix-lookup.cpp` takes a mode (`binary` or `prefix`), a sorted table file, a query file and an output path. All three files contain little-endian uint32 words on the benchmark host. For every query it writes the number of equal entries in the table. The prefix mode records 4,097 starting offsets (16,388 bytes) for the top 12 bits of each 31-bit key. Both modes find the lower bound and scan equal entries.

```sh
clang++ -O3 -mcpu=native -std=c++20 prefix-lookup.cpp -o /tmp/m31-prefix-lookup
/tmp/m31-prefix-lookup prefix /tmp/m31-public-x.bin queries.bin counts.bin
```

The `prefix-times.csv` timer starts with the same sorted table and query array already in memory. It includes directory allocation and construction and all queries, and ends before output serialization. Table generation, file reads, input validation, answer-array allocation and directory destruction are outside this timing. Each case used 12 rounds with balanced mode ordering and fresh processes. For each basis and mixture, Python's `random.Random(2026112414)` generated 65,536 queries. Uniform queries use `randrange(2147483647)`. For the half-planted mixture, odd-numbered positions (zero based) instead draw from the sorted table with `choice`. Shorter cases use prefixes of these streams. Every individual answer was compared with a Python frequency count. The numerical crossover applies to these two fixtures and these query streams.

## Setup-charged hash comparison

The `hash` lookup mode indexes the full 31-bit key and its count in a linear-probed array. A zero count marks an empty slot. For 28,033 entries, the array has 65,536 slots of eight bytes each (512 KiB). It charges allocation, initialization, insertion and querying to the same timer used for the binary and prefix arms. Each query returns its exact multiplicity.

Run `python3 hash-panel.py` to replay the initial comparison and `python3 hash-panel.py --confirm` for the fresh-stream confirmation at 262,144 queries. Both write CSV to standard output. The archived rows are in `hash-times.csv`. The driver builds the binaries, verifies both fixture digests, balances arm order, and checks every answer against an independent frequency count. Uniform and half-planted streams are reported separately.
