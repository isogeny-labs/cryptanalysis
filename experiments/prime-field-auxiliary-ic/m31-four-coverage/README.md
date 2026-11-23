# Four-summand coverage of the public M31 signed basis

The frozen 195 target abscissae have SHA-256 e7ddb831369de7724ca977022707d844512ccfe0191cb2c5daf5a22ad84a6203 as decimal lines. Both signs are available, repeats and cancellation are allowed, and infinity is counted separately. The curve has odd prime order 2147505293, so each finite abscissa corresponds to exactly two opposite points. The union through arity four covers 783104640 of the 2147505292 finite points (36.465784%); the exact-four support covers 776833440 (36.173761%). The gap from the formal radius-four ceiling after removing the zero vector is 190842880 finite points.

The counter enumerates sorted signed multisets, orienting each up to global negation so the first occurrence of its least-indexed generator is positive. Negating all summands negates the sum and preserves the abscissa. A bitset records only finite abscissae. The arity-specific and cumulative bitsets discard multiplicity. Reversing the input order changes the grouping and orientation, and reproduced all counts. At arities two and three the exact counts agree with the earlier independent affine census. The small-set checker uses a separate full-point addition implementation, including a positive control of three successive multiples.

From the experiment parent directory:
```sh
c++ -O3 -std=c++17 m31-four-coverage/census.cpp -o /tmp/m31-four-census
/tmp/m31-four-census < m31-basis-mask/coordinates.txt
/tmp/m31-four-census reverse < m31-basis-mask/coordinates.txt
python3 m31-four-coverage/check.py /tmp/m31-four-census
```

Orientation.lean verifies the cardinality identity for disjoint pairs of opposite group elements. FourTerm.lean in the neighboring m31-smooth-triples directory verifies the coefficient-vector ceiling. The exact support sizes are results of exhaustive native enumeration.

## Cardinality-matched controls

Run `python3 m31-four-coverage/matched.py /tmp/m31-four-census` after building the binary as above. Append `reverse` to repeat with the opposite generator order. The three controls use the previously specified seeds 0, 1 and 2 and the same sorted pool of 16342 liftable points from the parent auxiliary fiber. Each has 195 generators, with signed summands and repeated generators allowed. In matched.csv arm 0 is the smooth basis; arms 1 through 3 correspond to the three seeds. The final column counts finite points simultaneously in both radius-four supports.

The smooth radius-four support exceeds those three exact control sizes by 123332, 395234 and 146224 finite points, respectively (0.00574 to 0.01840 percentage points of the finite target population). These three comparisons do not estimate a population-wide smoothness effect. The union of the smooth support with each individual control covers 59.63124%, 59.62307% and 59.62969% respectively, with two separately constructed bases. Every count including the intersections matched in reverse order.

For scale, if two supports A and B include infinity, their average intersection over all translations of B in the full group is |A||B|/|G|. Orientation.lean proves the double-counting identity. The intersections in the unshifted comparisons differ from those translation averages by approximately -18420, -15729 and +430 points. The average uses the group order 2147505293 and adds infinity once to each finite support count.

## Multiplicity of reduced signed representations

Run the same counter with the argument `multiplicity` and the frozen coordinates on standard input. Each representation is an integer coefficient vector of absolute sum at most four. Permutations and cancelling pairs leave the coefficient vector unchanged. Repeated occurrences with the same sign are allowed. The recursion skips an adjacent sign change on the same generator and orients the first nonzero coefficient positively. A checked four-bit counter per abscissa aggregates the resulting sign pairs. The separate identity count starts with the empty vector. No bin overflow occurred.

The bins in multiplicity.csv count finite group points. Their sum is 783104640, and their multiplicity-weighted sum is 973947520. Adding the unique identity vector recovers the previously proved radius-four count of 973947521. The full histogram reproduced in reverse basis order. The small oracle in check.py computes explicit signed coefficient tuples and groups them by full affine point on three controls. Orientation.lean proves that opposite outputs have equal multiplicities over a negation-stable domain with odd evaluation.

## Universal nine-term bound

Let S be the full radius-four ball, including the identity, and P the frozen generator with x=3. The union T of S, P+S and -P+S has 1586841250 finite points, or 73.89231% of the finite group. Every member uses at most five signed summands. To reproduce, pass `translate 3` to the census binary with the frozen input. The first four lines use the column order in counts.csv and the last line gives the translated union's finite size. The reverse generator order reproduced all five lines. The independent small oracle explicitly constructs both translates on three smaller bases.

Including the identity gives |S|=783104641 and |T|=1586841251. For any g, the intersection of S with g−T has at least |S|+|T|−2147505293 = 222440599 elements. Each yields a distinct ordered group-element split with the first part in S and the second in T. Consequently every group element has a representation using at most nine signed generators. Counts of reachable points through four rule out a diameter of four. The resulting diameter interval is [5,9]. This is an existence statement and supplies no time bound for finding a representation.

Diameter.lean verifies the general covering implication and the numerical nine-term and overlap corollaries with explicit group order, set cardinality and reachability hypotheses. The set cardinalities come from the native census, independently replayed in the two orders.

## Exact diameter of the frozen signed basis

The first 30 generators in the frozen coordinate order suffice as anchors. Taking the union of the radius-four ball and its translates by both signs of each anchor covers all 2147505292 finite points. The identity is already in the original ball. At 29 anchors two finite points were still outside this particular union. The count of 30 is sufficient in this order; the minimum number of anchors was not measured.

The radius-four count of 783104640 finite points implies that exactly 1364400652 finite points require five signed summands. The finite-point counts by minimum length 1 through 5 are 390, 76050, 9864012, 773164188 and 1364400652. In particular the signed Cayley graph has diameter exactly five. The mean minimum length over uniform finite points is 9944404538/2147505292.

Run the census with `five` or `five-reverse` and the frozen input on stdin. Both enumerate the same anchor order; the reverse mode changes the internal generator order of every underlying sumset computation. The output in five.txt begins with the four unshifted counts and records the cumulative finite count after each anchor. At full cardinality the current program independently scans all M31 abscissae and compares the visited bit with square-residue membership for the target cubic. This check uses a separately generated table of all squares and a finite-difference cubic recurrence. check.py also compares all anchor counts against explicit point addition and the final small-set support against direct five-summand enumeration.

Diameter.lean proves the exact-diameter implication from a full union of translates and a proper radius-four subset, the passage from abscissae to both ordinates, the half-field square-table criterion, and the cubic scan recurrence. The full-sized set membership and counts are computational premises established by the native runs. The diameter calculation does not measure single-target search time.

## Exact four-step random walk

Choose each of four steps independently and uniformly from the 390 signed generators, with replacement. Run `walk-four` on the census binary with the frozen abscissae on stdin. The histogram includes the group identity. Each bin gives the number of group elements with the stated number of ordered walks. Reversing generator order reproduced the complete histogram. The independent oracle propagates integer path counts by one affine addition at a time on three smaller bases.

The counter weights a sorted multiset by the number of its permutations. A reduced four-word multiset uses its multinomial weight. A cancelling pair leaves either two copies of the same signed generator (12m−8 ordered words) or two distinct non-opposite signed generators (24m−24 ordered words) for m generators before signing. The empty coefficient vector contributes 12m(m−1)+6m ordered words. The count sums to 390^4 = 23134410000. This walk model differs from uniform sampling of reduced signed coefficient vectors.

For a bin with k paths and n endpoints the contribution to the total variation deficit is n times max(0, 390^4−k|G|), divided by 390^4 |G|. The exact total variation distance is 3963950350533370879/6210158490679016250 = 0.638300996099. Absent points alone contribute 0.638262385880. The squared-count sum is 2640817050634. By symmetry and independence of the two four-step halves, the eight-step return probability is this sum divided by 390^8, approximately 4.93425e−9 or 10.5963 times the uniform identity probability. WalkFour.lean checks the histogram arithmetic in the kernel and proves the symmetric endpoint pairing identity. Enumeration supplies the bins.

## Five-step mixing estimate

Run `walk-five-sample` with the frozen basis on stdin. The program builds the same per-point four-step counts used in the exact histogram and checks their total mass. For each sampled group point g it sums those counts at g+b over all 390 signed basis steps b. Sign symmetry makes this the exact number k of length-five ordered paths to g. The sample average of max(0,1−|G|k/390^5) estimates total variation distance. WalkDeficit.lean proves the positive-deficit identity and the equality under step sign exchange.

Each of four fixed MT19937 seeds supplies 65536 group draws. Uniform 32-bit words encode an abscissa and an ordinate sign. Rejection leaves exactly one encoding per group point, including one for infinity. Seeds 31, 211, 390 and 195 gave five-step estimates 0.079700, 0.079507, 0.079254 and 0.079370. The pooled estimate is 0.079458; the same points give 0.637970 at four steps versus the exhaustive 0.638301. The deficit lies in [0,1]. Under an independent uniform-draw model the two-sided 95% Hoeffding half-width for 262144 draws is sqrt(log(40)/(2*262144)) = 0.002653. The actual seeds are fixed for replay, and the interval describes sampling uncertainty under that model.

The two return-path counts are exact and independent of the sample. There are 4800 ordered five-step returns to the identity and 884536380 six-step returns. Divide by 390^5 and 390^6 respectively for the return probabilities. The complete CSV reproduced with the generator order reversed. Three small full-point oracles check five-step counts at the identity and six-step counts by independently accumulating five-step paths and summing over signed basis points.
