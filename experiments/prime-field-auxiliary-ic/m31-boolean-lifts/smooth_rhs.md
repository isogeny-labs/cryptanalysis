# Smooth coordinate signatures and target lifts

Compile smooth_rhs.cpp with clang++ -std=c++17 -O3 and run locally. The domain is every positive integer less than 2147483647 whose prime factors are at most 89, without rotations. For each coordinate x, compute the canonical residue r of x³+2x+14 and test whether r is a square. The input signature records the exponent of each of the 24 primes in x modulo two. A deterministic classifier given only the signature must return one label per bucket. Summing the smaller class count in each bucket gives the attainable minimum number of classification errors on this domain. Only wholly negative buckets can be rejected if every lift must be retained.

The second test looks for r in the sorted list of all positive 89-smooth integers. Whenever it is present, the parity of the nonsquare-prime exponents in the factorization of r gives its square class. The reported count uses the canonical positive representative and does not bound alternate representatives. The census checks this label against direct field exponentiation on every such r, confirms uniqueness of the coordinate enumeration, and verifies the previously established population and lift totals.

The Lean theorem smooth_square_witness in CubicSpan.lean independently checks a minimal kind of collision: x=1 and x=9 differ by a factor of 3² and have opposite target lift labels. The full census counts are native computations. No table construction or lookup speedup is assumed.

## Signed rotations and reciprocals

Run the same program with the argument orbits. The four bits in match_mask mark a smooth representative among rotations of r, of −r, of its reciprocal, and of the negated reciprocal, respectively. The program indexes reciprocal orbits of smooth integers and queries the orbit of r to avoid inverting every query. Stripping powers of two from the indexed integers preserves the orbit. It checks for conflicting labels within each table and verifies every matching route independently against direct exponentiation, including overlapping routes. The zero case is checked and excluded for this domain. SmoothOrbit.lean proves the quadratic-character identities used by the rotation, inversion and negation rules.

Each coordinate is counted once per mask. The nested unions for mask bits 1, 3 and 15 cover 59807, 118910 and 235328 coordinates. The combined table covers 117734 lifts and 117594 nonlifts. Its 6.118% coverage is a ceiling on the fraction of direct label tests that this particular rule can replace on this smooth-input domain. The census does not charge a setup or lookup time.

## Charged label throughput

Build with Apple Clang 21, -O3 -mcpu=native -std=c++17. Run with the argument timing. Three fresh local M4 Pro processes timed six paired traversals each, alternating arm order. The common coordinate list is already generated, in identical order for both arms. Both arms compute the cubic right-hand side and emit a byte per coordinate. The direct arm invokes the same 30-square arithmetic used by the hybrid on a miss. The hybrid combines rotations and negations in a single 31-word min/max scan, then probes one packed two-bit entry. The same table stores reciprocal representatives. A miss triggers direct squaring. Every pair verified identical output vectors and exactly 235328 hits.

The 256 MiB index setup is measured from allocation through representative insertion, once per process. Output allocation and verification are outside the timers. CSV setup values repeat on each row only to identify the single charged setup. For warm comparisons exclude setup; for one cold traversal add it once to the first hybrid time. Each process uses the same coordinate set on a shared unpinned host. Hot and cold comparisons both favor direct arithmetic. This is a complete label pass over the smooth-coordinate population and excludes collector work.

## Complete census with bucketed lookup and field arithmetic in blocks

The default executable partitions the sorted coordinates by their top 19 bits and stores 524289 offsets (2 MiB plus four bytes). A query searches just the rows with the same top bits and still compares the full coordinate. The offsets are built in one pass over the sorted rows. Cubic values are classified in blocks of 32 with the same 30 successive field squarings. The implementation widens each product to 64 bits and folds at bit 31. Apple Clang reported vectorization width 4 with interleave count 4 for the inner squaring loop. The final partial block uses its actual length.

On one Apple M4 Pro with Apple Clang 21.0.0, all six orders of the three builds were run. Each observation is a complete fresh process including generation, sort, directory and bucket allocation, cubic evaluation, lookup, aggregation and output. The table reports medians in seconds. Compilation is outside the measurements.

| Build | Wall | User + system CPU |
|---|---:|---:|
| Original, f9c7b49e7 | 1.051354 | 1.046992 |
| Directory only, 4f9bb3425 | 0.585722 | 0.582144 |
| Directory and field arithmetic in blocks | 0.401838 | 0.393886 |

The median of the six within-block original/final wall-time ratios was 2.655. All 18 outputs matched smooth_rhs.csv byte for byte. A separate untimed cross-check compared each new label, lookup membership and matched row against the scalar square test and full-range binary search over all 3846525 coordinates. Run the default executable after compiling smooth_rhs.cpp with `clang++ -std=c++17 -O3 -mcpu=native`. The raw block and position data are in smooth_rhs_directory_timing.csv.

Directory.lean checks the sorted bucket boundaries, membership equivalence and last offset index. The existing ../m31-field-ffi/Fold.lean checks the field product identity and word bounds. This measures the complete public smoothness census on one shared host. Collector runtime and other processor architectures are outside this measurement.

## Packing the parity-signature counters

A smooth integer x has a parity bit for each of the 24 primes in the census. Multiplying just the primes with odd exponents gives a squarefree divisor of x. Conversely, that squarefree product itself realizes the signature whenever it is below p. Exactly 266975 signatures meet this condition.

The index splits each mask into two 12-bit halves. It ranks the low halves by squarefree product. For a given upper product h, all allowed low halves form the prefix with product at most floor((p−1)/h). Concatenating those prefixes gives a unique slot per realizable signature. The rank and offset arrays use 24580 bytes, and the counters use 2135800 bytes. The former direct array used 134217728 bytes. SignatureIndex.lean proves the prefix threshold, saturation property and injectivity of the offset-plus-rank construction.

A fresh M4 Pro comparison used 30f4fdf81 as the control with the same directory lookup and batched arithmetic. Eight alternating-order pairs timed the full default census, including the new index construction. Both binaries used Apple Clang 21.0.0 with `-O3 -mcpu=native -std=c++17`. Wall time includes invocation through `/usr/bin/time -lp`; peak resident size and user/system CPU come from that utility. The in-process counters do not measure filesystem cache.

| Complete process | Median wall (s) | Median CPU (s) | Median peak RSS (bytes) |
|---|---:|---:|---:|
| Direct signature array | 0.406533 | 0.39 | 200507392 |
| Packed signature array | 0.381257 | 0.37 | 68526080 |

All 16 outputs matched the archived CSV. The median within-pair speedup was 1.070×. A separate exhaustive check used unsigned 128-bit squarefree products to classify all 16777216 masks and checked the compiled index's feasibility boundary, absence of collisions, and use of every slot. An address/undefined-behavior sanitizer run reproduced the same CSV. The raw process measurements are in signature_index_timing.csv. These results apply to the public census.

## Does a parity signature predict a withheld lift?

The 24 parity bits give 266975 nonempty groups, including 95824 singletons. Choosing the majority label after observing every label in each group gets 2194269 of 3846525 coordinates right (57.0455%). For each coordinate in turn, remove its label, predict from the other members of its group, and score a tie as half correct. The resulting score is 3839141/2 correct (49.9040%). There are 317063 tied votes, including singletons. Always predicting a lift scores 50.0198%. This leave-one-out score is exact for the archived population and tie convention.

As a second check, among all 869861730 unordered pairs of distinct coordinates sharing a signature, 434923282 have the same label (49.9991%). This statistic weights larger groups by their number of pairs. Neither scoring rule measures collection time.

Under an independent fair-label model with precisely the observed group sizes, the expected fitted majority score is 2194387.96 with standard deviation 584.81. In a group of n labels, the fitted score equals (n+|S|)/2, where S is the sum of n fair signs. The recurrence for expected |S| adds Pr(S=0) at each step, and E[S²]=n. The model provides a reference for the bias from fitting and scoring on the same labels. The actual curve labels are deterministic.

Compile the census as above and run `./smooth_rhs signature-holdout | python3 signature_holdout.py` (use the name of the compiled binary). The scalar, direct-index implementation from f9c7b49e7 with histogram output produced the identical 6034 data rows. Holdout.lean checks the per-group scoring identity, the fair-sign recurrence step and the comparisons between the exact aggregate scores.

## Graph of square-multiple coordinates

For each of the 24 smoothness primes q, connect a smooth coordinate x to the integer q²x whenever q²x < p. Both endpoints have the same exponent-parity signature. Repeated divisions by prime squares lead to the squarefree part of each coordinate, so each connected component of the undirected graph has one squarefree root. The enumeration contains 266975 such roots.

Every one of the 6748424 directed edges is included once. Copying the source lift/nonlift label gives 3375622 correct (50.0209%). Even choosing the best Boolean rule separately for every prime after seeing all labels gives only 3379303 correct (50.0754%). A separate best constant for each prime gives 3378048 correct. Knowing the source label therefore adds at most 1255 correct decisions on this panel, or 0.0186 percentage points. For 12 of the 24 primes the source label adds zero correct decisions. Every cell of every table is positive. Even allowing abstention, a rule using only the multiplier prime and the source label cannot certify a single context without an error. The best individual fitted accuracy is 20803/41222 (50.466%) at q=71. These are finite-population ceilings for rules with these two inputs, weighted by edges. They do not require independent edge observations. The edge set uses integer products below p, with no modular wrapping.

Run the census binary with `square-edges` to reproduce square_edges.csv. The C++ code scans from source to destination in sorted order. Run `python3 check_square_edges.py` with NumPy and python-flint to check the reverse division from every destination, recompute lift labels via the Jacobi symbol, and compare all 96 cells with both the CSV and the Lean inputs. SquareEdges.lean verifies the optimal rule for any 2-by-2 table and checks the pooled counts.
