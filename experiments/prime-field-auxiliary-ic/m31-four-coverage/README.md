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

## Returns forced by sign cancellation

A formally balanced word uses each of the 195 named generators equally often with both signs. All such words return to the identity in any abelian group. To add one generator to a balanced word of total length 2k, place its 2j occurrences at choose(2k,2j) positions and select the positive half in choose(2j,j) ways; the other positions form a shorter balanced word. Balanced.lean checks the resulting integer recurrence through eight steps. Run `python3 balanced.py` to cross-check by multiplicity partitions, by direct enumeration on one through three generators, and against the archived histogram and return counts.

At six steps, 882956100 of 884536380 returns are formally balanced (99.8213%). At eight, 2391959893050 of 2640817050634 are balanced (90.5765%). The remaining ordered returns can include permutations, sign reversals and multiples of the same relation.

The comparator in balanced.csv draws each of the 195 named generators independently and uniformly from the prime-order cyclic group, with replacement. For every nonbalanced word of length at most eight, some signed coefficient is nonzero modulo the group order. Holding the other generators fixed leaves exactly one value of that generator yielding the identity; Balanced.lean proves the unique-completion field identity. Linearity of expectation therefore gives (390^k−balanced)/2147505293 for the expected number of nonbalanced returns at length k. The fixed basis gives 0.96445 times this expectation at six and 0.99854 times at eight. This comparison of aggregate counts leaves correlations between word evaluations and the rank of their coefficient vectors unresolved.

### Five-step coefficient classes

Run the census with `five-prefixes` on the frozen coordinates. Reversing the coordinate file reproduces five-prefixes.csv. The counter counts each reduced four-letter multiset up to global sign if its endpoint has a basis abscissa. Each such endpoint admits one completing signed letter. The low-16-bit table only skips impossible abscissae. Every accepted abscissa passes a full-width comparison.

The histogram has 100 prefixes of permutation weight 24 and zero of weights 1, 4, 6 and 12. Every five-step return is reduced, since deleting a cancelling pair would give a three-step return and the frozen basis has none. If a generator repeated in a five-step return, some deletion would leave a repeated generator in a completable prefix. That prefix would have weight below 24. Thus all five generators are distinct. Each class up to global sign produces five different prefix classes by deletion. Unique completion prevents two different classes from sharing a prefix. The 100 prefixes therefore give exactly 20 classes. As a check, two signs and 120 permutations per class reproduce all 4,800 ordered returns.

Over the prime subgroup-order field these classes span at most 20 dimensions. A nonzero linear map from the 195-dimensional coefficient space to the one-dimensional group has a 194-dimensional kernel, leaving at least 174 dimensions outside that span in the quotient. The census does not measure the exact rank. FiveClasses.lean checks the orbit arithmetic given the stated encoding and word count, and the general span bound given the representative count. The native census and its interpretation supply those hypotheses. The independent small-basis checker reconstructs prefix multiplicities from signed coefficient vectors and full affine points, including a basis of successive multiples.

### Shared denominators in the native census

Each adjacent pair of signed generators has the same abscissa. The visitor computes one reciprocal for the pair, with separate handling for infinity, doubling and cancellation. Four independent prefix products share one field inversion. The fixed addition chain in inverse_nonzero raises the product to 2147483645. PairInversion.lean covers the shared reciprocal off the diagonal, the reverse-product step and the exponent of the chain. Native exception handling and C++ integer arithmetic are exercised by the independent affine-point checker.

On an Apple M4 Pro with Apple clang 21.0.0, six interleaved process launches per build gave median wall times of 2.632 s for the parent, 1.771 s for four lanes with generic exponentiation and 1.731 s with the addition chain. Median child CPU times were 2.625, 1.765 and 1.726 s. The parent-to-final wall ratio was 1.52. inversion-timings.csv retains every timing, including two slower wall observations of the final build. This measurement covers the complete five-prefix census of the frozen coordinates, on one shared arm64 host. PCC-20261123-37b587 records the local measurements. [pcc:unverified]

For reproduction, compile census.cpp with `c++ -std=c++17 -O3` and run `five-prefixes` with m31-basis-mask/coordinates.txt on stdin. Compare stdout byte-for-byte with five-prefixes.csv. The base source is commit 868662e66215923c2734caa08b51f4ac328d6921. For the paired lane controls, replace the call to inverse_nonzero(product) with power(product,p-2) and set the lanes constant to 1, 4 or 8. The first panel balances the four builds across launch positions. The confirmation panel uses all six orders of the three builds. Both panels include process startup, input and output. The runner collected child user plus system CPU time in the confirmation panel only.

### Two-step hash screen for the five-prefix histogram

For a three-step endpoint T, a fourth signed generator b can reach a signed generator c only if T = c − b. The signed basis contains −b, so T must belong to the two-step support. The program enumerates this support once up to global sign, including cancellation to infinity. It marks the low 22 abscissa bits in a 512 KiB bitset. A missing bit skips the entire final expansion. A present bit retains the existing fourth-step arithmetic, ordering, permutation weight and full-width endpoint test. Collisions can only retain extra expansions. This argument also covers repeated steps and bases with short relations.

On the frozen 195-coordinate basis a separate counter observed 44,781 retained nodes in 4,943,315 probes, in both generator orders. Eight fresh local launches per binary on the Apple M4 Pro gave median wall times of 1.726726 s for f394d26ad and 0.046707 s with the filter. Median child CPU times were 1.720574 s and 0.045208 s. All 16 outputs matched five-prefixes.csv byte for byte. Each process built its table from the supplied coordinates. Forward and reverse input each occupied both launch positions twice per build. PCC-20261123-e611fb records the timing claim. [pcc:unverified]

Compile each version using Apple clang 21.0.0 with `c++ -std=c++17 -O3 census.cpp` and run `five-prefixes` with the coordinate file on stdin. The per-launch measurements are in pair-filter-timings.csv. PairFilter.lean proves the necessary two-step membership, the effect of choosing sign representatives, and preservation of a weighted histogram bin when discarded nodes contribute zero. The affine-point checker exercises the compiled implementation separately. This benchmark covers one aggregate graph statistic.

### Smoothness and five distinct labels

The simple-five mode counts zero-sum classes using five distinct generator labels, modulo sign and permutation. It visits four-label prefixes of weight 24, looks up the endpoint abscissa, and accepts only when the completing label exceeds the four prefix labels. Each five-label support has one largest label; removing it leaves exactly one eligible prefix up to sign. Distinct basis abscissae and nonzero ordinates give a unique completing sign. LargestCompletion.lean checks the largest-label argument. The full affine checker independently enumerates all sign assignments on small bases, including a positive control using multiples 1, 2, 3, 4 and 10.

Run `python3 m31-four-coverage/matched.py /tmp/m31-four-census five-panel` and append `reverse` to repeat. Arm zero is the frozen smooth basis. Arms 1 through 256 sample 195 labels without replacement from the same 16,342 liftable auxiliary points used in the earlier controls, with seeds 0 through 255. The endpoint is the number of distinct five-label classes. The smooth basis gave 20. The original three controls gave 19, 12 and 17. Across all 256 control draws, the median was 17, the mean 16.75 and the range 7 to 29. Forty-seven controls exceeded the smooth count and another 20 tied it. All 257 rows agreed in reverse order. PCC-20261123-28506a records the local panel. [pcc:unverified]

The fraction 67/256 describes these controls. The smooth basis was selected deterministically. The comparison measures one kind of short relation and leaves both linear independence and end-to-end collection time open.

### Independent rank from coordinate deletions

On the frozen smooth basis the five-distinct-label classes have rank 20. On the matched seed-3 basis they have rank 21. Seed 3 was chosen after the 256-control panel as the first control with more classes than the smooth basis. This is an example of a matched basis with a higher independent yield, and selection prevents using it to estimate a typical rank difference. Relative to the 194-dimensional kernel, these classes leave quotient dimensions 174 and 173 respectively. PCC-20261123-3abf2a records the measured premises. [pcc:unverified]

Removing a generator keeps exactly the classes with a zero coefficient on its label. A drop of one in the full-basis count identifies a coordinate used by one class only. Accept the coordinate if adding it to previously selected deletions removes one further class. The cumulative drops certify that the selected coordinates belong to different classes. For the smooth basis there are 19 such coordinates and one residual nonzero class. For the control all 21 classes have distinct private coordinates. In a zero linear combination, evaluation at each private coordinate forces that row's coefficient to vanish. Any remaining row then has coefficient zero because its entries include a unit. This argument is valid over the subgroup-order field and does not require knowing the signs of the entries.

Run `python3 m31-four-coverage/private_pivots.py BINARY` and repeat with `reverse`. Add `seed3` to either command for the control. The two CSVs use zero-based indices into the original generator order. For a second counting route, compile census.cpp from f394d26ad and run `python3 m31-four-coverage/replay_private_pivots.py OLD_BINARY`, with an optional `seed3`. This checks three-step absence by direct affine arithmetic and exhaustively counts four-letter prefixes on every listed deletion. The old counter uses neither the two-step hash screen nor the largest-label test. DeletionCount.lean proves the implication from a count drop to a unique nonzero row. PrivatePivots.lean proves the field-rank conclusion given the private coordinates and a nonzero residual row. The census supplies the cardinality premises.

### Deterministic mixing bound from the four-step histogram

For the frozen walk with 390 equiprobable signed steps, every nontrivial eigenvalue has absolute value below 0.9641. Starting at any point, the total variation distance to uniform is at most 1/4 after 54 steps, 1/100 after 142, 1/1000 after 205 and 1/1000000 after 394. These are sufficient lengths conditional on the full histogram. The five-step sample estimates a distance at a particular time. Neither calculation measures collector wall time. PCC-20261123-4b7100 records the bound. [pcc:unverified]

Let N be the prime group order, W = 390⁴, and w(g) the ordered four-step path count. Each nontrivial character visits every N-th root of unity exactly once. Write r for the smaller unsigned distance of its exponent from zero modulo N. The one-step eigenvalue λ is real by sign symmetry, and independence gives λ⁴ as the average of cos(2πr/N) with weights w(g)/W.

1. For j from 1 through 24, fewer than jN/128 units of folded distance occupies exactly c = 1 + 2 floor((jN−1)/128) endpoints. For any c slots the sum of weights inside is at most c k + Σ max(w(g)−k,0), at any nonnegative clipping level k. Subtract this bound from W to lower-bound the mass outside. The Python replay fills slots in descending weight order. The Lean replay uses clipping levels 48, 24, 12 and 0, and reaches the same integer bound.
2. At a point outside that arc, put x = 3j/128 and t = πr/N. Then 0 < x ≤ t ≤ π/2, and 1−cos(2t) = 2 sin²(t) ≥ 2(x−x³/6)². Round the last expression down in units of one millionth. The rounded prices increase across the 24 thresholds. Multiplying each price increment by its outside mass and summing gives at least 3147515720318076 units of lost cosine over all paths. Telescoping ensures each endpoint pays just the price of its largest crossed threshold.
3. Dividing the loss by 1000000 W gives λ⁴ ≤ 1665574523306827/1927867500000000 = B. From the histogram the four-step chi-squared divergence is C = N Σw(g)²/W² − 1. Parseval identifies C with the sum of the eighth powers of the nontrivial eigenvalues. For t ≥ 4, Cauchy–Schwarz and the eigenvalue bound give 16 TV(t)⁴ ≤ C² B^(t−4), yielding the thresholds above. Translation invariance makes the bound uniform in the starting point. [Transitive-chain inequality, Levin and Peres, Lemma 12.18](https://pages.uoregon.edu/dlevin/MARKOV/markovmixing.pdf)

Run `python3 m31-four-coverage/spectral.py` to recompute from walk-four.csv with rational arithmetic. WalkFour.lean kernel-checks the histogram sums, threshold prices and final integer comparisons. ArcBound.lean proves the clipping, sine and weighted summation inequalities. The character argument and its application to this walk are the mathematical derivation above.

### Profile after the two-step screen

A two-second macOS sample of repeated five-prefix calls put 1,306 top-of-stack samples in the signed visitor and 77 in field inversion. The visitor formerly computed the ordinate and permutation weight and called the next recursion level before rejecting a three-step endpoint. It now tests the abscissa first. Each endpoint marks two positions in the same 64-bit word of the 512 KiB table. Bits 6 through 21 of the abscissa select the word. Bits 0 through 5 and 22 through 27 select the positions. A successful lookup requires both marks. Later insertions and coincident marks preserve acceptance of every inserted abscissa. On the original basis 4,274 of 4,943,315 probes triggered a fourth expansion, compared with 44,781 for the preceding single-mark build. [pcc:unverified]

The first panel compared the parent, the early abscissa test alone, two separate 512 KiB tables, and the two-table variant with compile-time recursion depth. Their median five-prefix wall times were 46.82, 37.58, 21.52 and 22.27 ms. The confirmation panel compared the parent, two tables, and two marks in one table. Each build occupied each launch position equally in each mode and orientation. For five-prefixes the medians were 64.02, 35.60 and 36.91 ms. For simple-five they were 60.07, 34.38 and 34.20 ms. Each measurement charged startup, allocation and table construction. The different parent times show why speedups here use the parent measured within the same panel. The single-table version retains the original memory allocation. PCC-20261123-d63ed2 records the local measurements. [pcc:unverified]

To reproduce the selected comparison, compile the parent ded800a14 and current census.cpp with Apple clang 21 using `-std=c++17 -O3 -g`. Use the two modes and basis order indicated by hash-confirm.csv with m31-basis-mask/coordinates.txt. The exploratory measurements are in hash-profile.csv. The simple-five outputs also reproduced every row of the 257-basis panel, and the default census reproduced counts.csv. HashScreen.lean proves the bit-preservation and filter-order identities; check.py exercises the native exceptional cases and small affine controls.

### Reducing the affine abscissa once

The visitor computes the new abscissa by reducing the nonnegative accumulator s² + (2p − x₁ − x₂), where s is the canonical slope. Each coordinate is less than p, so the 32-bit offset fits and the full accumulator is at most (p−1)²+2p. Split it at bit 31, add its two parts, and conditionally subtract p once. WordReduction.lean proves this agrees with reduction modulo p for every accumulator in the stated range. It checks the accumulator width, the offset congruences, and the wrapping 32-bit carry and borrow alternatives. Compiling the isolated abscissa expression with Apple clang 21 produced a widening multiply-add (UMADDL) and one conditional selection.

Using the frozen 195-generator fixture on the M4 Pro, the median within-round parent-to-selected wall ratios were 1.063 for five-prefixes, 1.078 for simple-five and 1.045 for the full radius-four census. The abscissa-only variant won 5/6, 6/6 and 5/6 rounds respectively. Fusing the ordinate as well gave a radius-four median child CPU time of 6.756 s versus 6.350 s for abscissa-only and 6.744 s for the parent. The production visitor retains its earlier ordinate formula. PCC-20261123-6aa109 records the local measurements. [pcc:unverified]

Compile the parent b78eb3cff and the selected source with Apple clang 21, `-std=c++17 -O3 -g`. Use the coordinate file in each recorded order and the indicated mode (no argument for radius-four). Each time includes startup and output. In word-confirm.csv the six rounds cover the six launch orders of base, fused_x and fused_xy. In word-screen.csv the carry and borrow controls independently replace one parent arithmetic function by the corresponding WordReduction.lean bit-vector expression. The exploratory and confirmation timings stand separately because they were collected in different runs on a shared host.

### Rust affine addition on the M31 field

The shared Rust Curve::finish_add method uses the bounded square-plus-offset reduction at B=31. Both the public checked batch API and its internal arithmetic path call this method. WordReduction.lean proves equality with separate modular subtractions on all canonical inputs. Eight field unit tests passed, including the new comparison against u128 remainders for 216 boundary triples.

The native-CPU internal benchmark, with zero exceptional slots, measured 428.94 ns for the parent and 406.15 ns for the candidate per batch of 64 additions. The median within-round speedup was 1.058×. For 1, 8, 32 and 64 mixed exceptional slots, the corresponding ratios were 1.055×, 1.041×, 1.039× and 1.026×. The independently compiled checked API panel measured 648.11 and 620.01 ns for ordinary batches, with a 1.046× median paired speedup. These timings measure point arithmetic. The full solver was outside the timed scope. PCC-20261123-154f09 records the local measurement. [pcc:unverified]

Use the existing batch_add_64_bench.rs with the parent 663fc4fb5 and the new field.rs. Compile with rustc 1.93.1, edition 2021, opt-level=3 and target-cpu=native on the Apple M4 Pro. Run lanes mode and take the first timing column after the exception count (the crate's reference batch implementation). Alternate parent-first and candidate-first across eight paired launches. Each case has 16 retained samples per launch, each timing 2,048 batches. For the checked panel, replace the reference wrapper's batch_add_inner call with batch_add(...).unwrap() and omit target-cpu=native. Take each launch median before computing within-round ratios. The two CSVs retain each reference timing. Compiler flags and validation cost differ between panels, so compare variants within each panel.

### Runtime batch width and shared tangent inverses in Rust

On arm64 the M31 affine batch routine now uses four independent denominator products for slices of 32 points or more. A forward pass records each slot's lane prefix. The routine inverts the product of the four lane totals once and walks the lanes backwards to recover per-slot reciprocals. A doubling with nonzero ordinate contributes its tangent denominator to the same batch. Infinity, inverse pairs and doubling with zero ordinate use the existing exceptional addition path. The dispatch uses one product for shorter batches. Modulo-four lane assignment handles partial final lanes without padding or additional scratch allocation.

The initial one-, four- and eight-lane comparison favored four lanes from size 32 on the ordinary and one-in-eight exceptional inputs (rust-width-screen.csv). A confirmation of the four-lane path alone exposed a slowdown on some all-exception inputs (rust-width-confirm.csv). The final comparison added shared tangent inverses. At 64 points, the parent/selected median paired ratios were 1.142× for ordinary additions, 1.492× for one exceptional slot per eight, and 3.693× when every slot was exceptional. At 256 points the ratios were 1.268×, 1.639× and 4.645×. Identity on the left, identity on the right, doubling and inverse pairs occur equally in the all-exception mix. The ratios describe these constructed inputs. The solver's distribution of exceptional slots and its end-to-end speedup remain unmeasured. PCC-20261123-27b383 records the measurements. [pcc:unverified]

In rust-tangent-confirm.csv, parent is 57065b59c, candidate uses four lanes above the threshold with the original exceptional fallback, and tangent is the published path. The panel runs all six launch orders twice on an Apple M4 Pro. Ratios are medians of within-round ratios. Set M31_FIELD_RS to an absolute field.rs path and compile rust-batch-width.rs with rustc 1.93.1, edition 2021, opt-level=3 and target-cpu=native. Each invocation regenerates and checks the same seeded points. Timings cover the internal batch call, input slice copy, and output barrier. Point generation and scalar-reference comparisons occur outside the timed loop. PairInversion.lean proves the product partition, reciprocal step and tangent denominator identities. The field tests also exercise scratch reuse across changing sizes and doubling a rational point of order two.

### Batch sizes exercised by the archived M31 workload

The archived protocol pins revision 6805d56f and 64 walk lanes. Its walk selects right operands from a 32-entry table. The direct two-summand routine repeats one left operand across twice the factor-base width. The archived two-summand panel includes widths 56, 58 and 71. The local arithmetic benchmark uses independently generated curve points with these operand patterns. It omits point selection, relation processing, setup and verification from the timed loop.

All six revision orders ran four times on the Apple M4 Pro with the preceding compiler flags. Each cell below gives median nanoseconds per batch across 24 rounds. The last column gives the median of ratios paired by round, which can differ from the ratio of the two column medians. Pass `shapes` to the benchmark to select these inputs. PCC-20261123-57ad5b records the local measurements. [pcc:unverified]

| Operand pattern | Width | Original 663fc4fb5 | Fused 57065b59c | Four lanes a82976381 | Fused / four lanes, paired |
|---|---:|---:|---:|---:|---:|
| Reused right table | 64 | 470.02 | 444.09 | 429.67 | 1.072× |
| Repeated left, signed right | 112 | 770.83 | 737.29 | 615.70 | 1.187× |
| Repeated left, signed right | 116 | 801.43 | 756.60 | 623.92 | 1.208× |
| Repeated left, signed right | 142 | 967.05 | 900.95 | 737.54 | 1.228× |

WalkShare.lean reads the archived E1 JSON and checks the walk fraction against the observed total, allowing 50 microseconds upward error for each printed walk time and 50 microseconds downward error for each total. For the 37 two-summand, five three-summand and four four-summand records, respectively, the upper bounds are 1.1705%, 0.0188% and 0.0009%. With all other elapsed work held fixed, these also bound the saving from eliminating the entire walk. Direct decomposition calls the batch kernel separately. Its share of decomposition time remains unmeasured.

### Matched two-summand encoding comparison

MatchedEncoding.lean replays 15 pairs from the archived E1 panel. Each pair agrees on column digest, attempted queries, matrix rank, relation count and recorded scalar. The timer is `ic_observed_total_s`. Each winning margin exceeds one printed tick, allowing for independent nearest-tick rounding. The following ratios use the five within-target circuit/direct time ratios for each base.

| Base | Direct faster | Circuit faster | Median circuit/direct | Range |
|---|---:|---:|---:|---:|
| Auxiliary | 5 | 0 | 1.359 | 1.303–1.794 |
| Multiplicative(126) | 1 | 4 | 0.949 | 0.895–1.172 |
| Torus7 | 5 | 0 | 1.558 | 1.320–1.677 |

The archived profiler brackets the entire decomposition call. Its attempted-query counter also includes points at infinity that skip decomposition. Across the direct records, median decomposition time per attempted query was 1,396 ns at width 112 (five records), 1,487 ns at width 116 (twelve), and 1,617 ns at width 142 (five). These denominators permit a throughput comparison. A breakdown between batch arithmetic, lookup and relation handling requires separate timing. The table summarizes an earlier source revision and predates the four-lane arithmetic change.

### Arithmetic and sorted membership at width 142

The local benchmark fills 142 slots with a single point, adds a table of 71 signed point pairs, then counts x-coordinates in a separate sorted table of 71 keys. The same 32 seeded inputs exercise both revisions. Scalar addition checks every batch before timing. All searches missed, so the lookup phase measures a full scan. Lookup alone reads precomputed sums. Combined timing searches fresh sums. The standalone arithmetic time includes the input fill.

Compile as in the operand-shape panel. Run `phases alc 2048`, permuting the three phase letters (arithmetic, lookup, combined) in all six orders twice and reversing revision order on alternating rounds and cycles. Each timing covers 65,536 batches. The table gives launch medians in ns/batch and median paired ratios on the Apple M4 Pro. PCC-20261123-18ade7 records the timings. [pcc:unverified]

| Phase | Fused parent | Four lanes | Paired parent / four lanes |
|---|---:|---:|---:|
| Arithmetic | 838.85 | 669.45 | 1.256 |
| Sorted membership | 379.26 | 378.56 | 1.000 |
| Combined | 1216.48 | 1049.32 | 1.165 |

The combined phase improved in 12 of 12 longer rounds. Median within-round (arithmetic + lookup) / combined was 0.997 for the parent and 1.000 for four lanes. The initial 24-round screen used 128 repetitions, exhibited much wider timing variation, and gave a 1.385 median paired combined ratio. Both raw panels are retained separately. The independent keys, repeated warm inputs and full miss scans limit transfer to a live workload. These timings exclude hit handling, setup, and outer-loop work.

### Exact bucket lookup on canonical 31-bit keys

A 1 KiB directory stores one of three values in each of 256 slots. An empty slot rejects a query. A singleton compares the entire key. A slot containing multiple distinct keys delegates to the sorted table. Two reserved u32 values lie above every canonical key. The multiplicative hash selects the slot. ExactBucket.lean establishes exact membership for the abstract three-state algorithm with any hash, including a constant hash, and allows duplicate keys.

The standalone membership-bench.rs compares lookup on the same keys in the same order. Each of 24 deterministic seeds builds a sorted 71-key table including 0 and p−1. For each hit mix, 32 batches of 142 queries repeat 256 times, with the two methods timed in alternating order. Every query is checked against binary search. The Apple M4 Pro native release build measured these median times in ns per batch. The speedups are medians of the 24 within-seed ratios.

| Hit fraction | Sorted | Exact bucket | Paired speedup |
|---|---:|---:|---:|
| Zero | 376.00 | 121.84 | 3.046× |
| One eighth | 368.72 | 113.63 | 3.263× |
| All | 378.63 | 157.41 | 2.367× |

There were 4–12 crowded slots per table. Directory construction from sorted keys took a median 46.85 ns over repeated builds. Adding each seed's measured build cost to one warm batch still favored the directory for all 72 seed/mix pairs. That calculation models setup amortization and does not measure a cold cache. Timings cover integer membership alone. The fraction of real inputs sent to fallback and the full arithmetic-plus-lookup effect depend on the key distribution. Compile with rustc --edition=2021 -C opt-level=3 -C target-cpu=native and pass round numbers 1 through 24.

PCC-20261123-301308 records the local measurement. [pcc:unverified]

### Combined arithmetic and exact lookup on the archived Torus7 columns

torus7_keys.py independently enumerates the depth-seven inverse tree, lifts and sorts the points, then reproduces the ordered signed-column BLAKE3 digest from both Torus7 arms on all five archived E1 targets. The 71 abscissas occupy 51 singleton slots and ten double-occupancy slots in the 256-entry directory. The other 195 slots are empty.

On the M4 Pro, median combined times per 142-point batch were 1048.45 ns with binary search and 831.50 ns with the exact bucket directory. The within-round ratio favored the directory in 24 of 24 rounds, with median 1.261 and interquartile range 1.243–1.272. Both variants use the a82976381 four-lane arithmetic and the same u32 keys. Every timed scan examines all finite results. A separate identity-point control exercises all 142 signed hits. Each round also checks scalar addition and both lookup answers on every input before timing.

Generate the keys with python3 torus7_keys.py (requires the blake3 module). Compile rust-batch-width.rs with the previous native flags and pass coordinate-lookup, the generated key file, and the round number from 1 through 24. Each round alternates method order, uses 64 seeded public points, then repeats their batches 1,024 times. The 218,112 coordinate slots across the distinct panels produced zero membership hits. Table construction, relation handling and the outer solver are outside the measurement. PCC-20261123-600ba9 records the local result. [pcc:unverified]

### Shared denominators for signed point pairs

For a broadcast input P and each pair Q, −Q, both ordinary secant slopes use the same denominator x(Q)−x(P). The signed-pairs.rs prototype puts that denominator into the four-lane product once and uses its reciprocal for both outputs. It accepts 71 finite representatives, writes all 142 full affine outputs in order, and handles equal abscissas and the identity separately. It also avoids initializing the output with 142 copies of the broadcast input. SignedPairs.lean proves the two affine formulas given the reverse-product invariant. The runtime check compares every output with scalar addition on 64 seeded left operands, all 142 signed table entries as left operands, and the identity.

Both timing arms use the same exact bucket lookup and the same digest-matched Torus7 columns. On the Apple M4 Pro the first 24 paired rounds favored specialization in 21 rounds, with a 1.311 median ratio. In 12 fresh longer rounds the general and specialized paths took median 997.30 and 802.94 ns per batch. The paired ratio was 1.267 (interquartile range 1.158–1.374), favoring specialization in all 12. The timed panels contained zero hits. These warmed component comparisons include both full-coordinate construction and lookup. They also include differences in input layout and output initialization. The timing cannot assign the gain exclusively to denominator sharing.

Compile rust-batch-width.rs with the preceding native flags and --cfg signed_pairs, using field.rs from a82976381. Run signed-pairs with the reconstructed key file, seed number, and repetition count. Seeds 25–48 use 1,024 repetitions. Seeds 49–60 use 4,096. Order alternates by seed. PCC-20261123-81f833 records the local measurements. [pcc:unverified]

### Direct comparison against the original affine batch

The original 663fc4fb5 arithmetic with sorted u32 lookup and the a82976381-based signed-pair prototype with exact bucket lookup ran on identical Torus7 inputs in each of 24 fresh rounds. The median paired original/specialized ratio was 1.975 (interquartile range 1.957–1.995), with the specialized path faster in all 24 rounds. Median ns per 142-point batch were 1250.64 for original/sorted, 1032.46 for original/bucket, 824.22 for newer general arithmetic/bucket and 633.76 for signed-pair arithmetic/bucket. Each timing includes full affine output and membership testing. The timed panels produced zero hits. This is a direct local component comparison. Setup, successful relation processing and end-to-end wall time require independent measurements.

Compile the common harness with the native flags above against each indicated field.rs revision. Enable --cfg signed_pairs only on the newer build. For seeds 61 through 84, run coordinate-lookup on the original build and signed-pairs on the newer build, passing the same key file, seed and 2,048 repetitions. Switch build order after every two seeds and method order inside each build on each seed. PCC-20261123-e90f07 records the measurements. [pcc:unverified]

SignedPairs.lean now proves the four-lane prefix and reverse passes as a recursive field-arithmetic model. Starting from any four nonzero lane products, one inversion recovers all four final reciprocals. For an arbitrary sequence of lane tags and denominators, the reverse traversal restores the reciprocals of the starting lanes and returns each nonzero denominator's reciprocal in input order, marking zeros for exceptional addition. The theorem includes arbitrarily interleaved, empty and unequal-length lanes. The Rust buffer implementation is checked against scalar addition in the harness.

### Starting from the 71 abscissas and counting finite hits

Each timed invocation lifts all 71 ordered Torus7 keys, prepares its tables, creates and drops working storage, and processes the indicated number of 142-point batches. Both builds begin with identical keys and pre-generated left operands. Key generation, program startup and the scalar oracle are outside the timer. Repeated invocations can reuse CPU caches and the allocator. In the positive mix the first and every eighth subsequent batch takes the sum of two distinct representatives as the left operand. SignedPairs.two_positive_slots proves why the two corresponding negative slots return those representatives. The benchmark checks the complete hit count against independent scalar additions.

| Batches per setup | Median paired speedup, random | Median paired speedup, positive mix | Positive hits per invocation |
|---:|---:|---:|---:|
| 0 | 1.008 | 1.008 | 0 |
| 1 | 1.149 | 1.156 | 2 |
| 4 | 1.427 | 1.390 | 2 |
| 16 | 1.971 | 1.704 | 4 |
| 64 | 1.854 | 1.935 | 16 |
| 256 | 2.007 | 1.943 | 64 |

The positive mix favored specialization on 20 of 24 seeds at both one and 256 batches. At 256 positive-mix batches the interquartile range of paired ratios was 1.757–2.172. Random one-batch timings had wider dispersion (0.854–2.081). The smallest measured nonempty workload favors specialization by the median. Each scan counts all matching coordinates and always finishes the batch. Relation creation and early termination are outside the timed work.

Use the two builds from the preceding anchor comparison in setup-batches mode, passing the reconstructed keys and seeds 109–132. Alternate build order by seed. Each build rotates the order of the six workload sizes by seed and times 4096/(batches+16) invocations using integer division. The earlier setup-checked-screen.csv uses seeds 85–108 and checked point negation during original table construction. The reported setup-batches.csv uses the internal negation used by the archived constructor. PCC-20261123-72ce02 records the measurement. [pcc:unverified]

### Generating the Torus7 public coordinate table

torus7-build.rs times primitive trace selection, recurrence enumeration, sorting, duplicate checks, polynomial checks on all 128 roots, and lifting onto the curve. The scalar control calls Curve::lift_x. The alternative computes curve right-hand sides in groups, then performs the 29 independent squarings needed in each lane to obtain a square-root candidate. Both check its square against the right-hand side and select the smaller canonical ordinate. All tested widths produced identical ordered points. The 71 resulting coordinate pairs reproduced the archived BLAKE3 digest 003eb1e8be482c521babf20c8c32062b838e400e3c49a7a1607f16f66b632af0.

In 32 confirmation rounds on the Apple M4 Pro, scalar lifting took a median 13.748 µs per complete table and width eight took 4.369 µs. The median paired ratio was 3.395 (interquartile range 2.455–4.161). Width eight won all 32 rounds. The initial balanced 24-order screen included the public scalar API and explicit widths one, four and eight. A second screen included eight, sixteen and thirty-two. These data support interleaving at this size. They do not settle the optimal width. Curve parameters and input trace selection are fixed, and repeated construction uses warm code and allocator state. This measures coordinate generation and validation. Constructing the full solver state entails additional work.

Compile with M31_FIELD_RS pointing to a82976381 field.rs and the native flags used above. Pass 0 for the scalar control or 1, 4, 8, 16, 32 for explicit widths. Each argument times 1,024 constructions. Pass points to print the scalar reference coordinates in digest order. FiberLift.lean proves the coordinatewise squaring exponent and that the final square test accepts exactly the squares in the M31 field, including zero. PCC-20261123-658887 records the local timings. [pcc:unverified]

### Sharing one lift between the curve and its quadratic twist

For the coordinate x on the base curve let r = x³ + 2x + 14. At −x on the twist with coefficients (2, −14), the corresponding right-hand side is −r. In M31, y = r^(2^29) has square either r or −r. Test both equalities and take the smaller canonical ordinate. At r = 0 both tables receive a point. FiberLift.lean proves the sign dichotomy, exclusive membership away from zero, exactness of both square tests, the twist polynomial identity, and that −1 is a nonsquare.

On the archived Torus7 fiber, 71 roots provided base points and the 57 others provided twist points. The base table reproduced the archived signed-column digest. Independent scalar point lifting on each curve checked both full ordered tables. A second fixture included a shared point of ordinate zero. The two output tables belong to different curves.

The timing control enumerates and validates the fiber once, then uses two eight-lane lifts. The joint method also enumerates and validates once, performs one eight-lane lift, and returns the same sorted pair of tables. In 32 alternating rounds on the Apple M4 Pro, median times per pair were 4.828 µs for separate lifts and 3.414 µs for joint lifting. The median paired speedup was 1.410 (interquartile range 1.407–1.420), with the joint method faster in 31 rounds. Compile torus7-build.rs as above and pass twist sj or twist js. Each method times 2,048 constructions per round. These measurements price preparation when both curve tables are requested. Usefulness of the twist points for the original curve's algorithm remains open. PCC-20261123-d6b5be records the local timings. [pcc:unverified]

### Can the twist enlarge an additive factor base?

The rational group of y² = x³ + 2x + 14 has order 2147505293. Its negative twist y² = x³ + 2x − 14 has order 2147462003 = 53 × 40518151. PARI ellcard computed each order independently. The standalone Python replay twist_orders.py verifies the point witnesses (1,1333027745) and (0,493947710), respectively. For each witness it checks its curve equation, its claimed order by multiplication and prime-factor tests, and uniqueness of the multiple in the Hasse interval. Lean proves the complementary point counts sum to 4294967296 by pairing the vertical fibers, and checks that the two numerical orders are coprime. The two individual orders enter the group argument from the point-count computations.

Consequently any additive homomorphism between the rational groups is trivial. Embedding both groups into a larger additive group also leaves a direct mixed sum ineffective. If a base target equals a sum of base and twist terms there, the total twist contribution must be zero, and the base terms alone give the same image. FiberLift.mixed_sum proves this for arbitrary homomorphisms into any common abelian group with coprime source sizes. The theorem applies to the 57 rational twist points in the preceding table and to all other rational points of this twist. It addresses direct additive mixing; constructions involving a nonlinear correspondence require a separate argument.

### Two different nonlinear maps on Torus7 abscissas

The elliptic-curve doubling map on x is D(x) = (3x²+2)²/(4f(x)) − 2x, with f(x) = x³+2x+14. DoublingClasses.lean certifies that f has no M31 root using a 30-step polynomial remainder chain for X^p and an inverse of X^p−X modulo f. This excludes all rational affine poles. The proof then establishes f(D(x)) = f(x) R(x)² with R(x) nonzero, and proves that every finite iterate of D preserves the square class test for every M31 abscissa. In the common x-coordinate convention from the twist lift, this closes transfer by repeated elliptic doubling.

The Torus7 fiber map g(x) = x²−2 behaves differently. The PARI replay torus7-map-audit.gp independently enumerates the 128 roots with polrootsmod. After one g step, 29 of the 57 twist-origin inputs have square f at the image. However, the 64 distinct image values include 41 reached from both base and twist inputs. After three steps all 16 image values are reached from both classes, and after seven steps all 128 inputs have the same image. Thus a classifier using only g³(x) cannot distinguish the input classes on this fiber. This does not bound methods that retain branch information. Running gp -fq on the supplied file also checks 32 elliptic doubling steps at all 128 inputs against the quadratic character.

### Retaining the seven branch choices

Bit j of a root's key records whether the canonical value of g iterated j times exceeds p/2, for j = 0 through 6. BranchKeys.lean kernel-checks all 128 keys, their distinct coordinate witnesses, the common terminal 340921998, the square-root witness on the selected curve and the nonzero right-hand side. The verified decision diagram and a 128-bit lookup mask agree on all keys. The label applies to members of this fixed fiber.

branch_diagram.py enumerates all 5,040 variable orders for reduced ordered binary decision diagrams without complemented edges. It independently checks the distinct-cofactor cost against explicit node construction for every order. The minimum is 36 nonterminal nodes, attained by 24 orders. Natural bit order uses 44. The median is 41 and the maximum is 45. Of 128 deterministic random controls with exactly 71 positive labels, 33 had a minimum of 36 or smaller, with median minimum 38. The sample gives little evidence of exceptional compression under this representation. Lean verifies the selected diagram and mask. The minimum and random-control counts use the Python replay.

The lookup timing distinguishes coordinates from available branch keys. Across 24 balanced local rounds on the M4 Pro, scanning 128 shuffled fiber members took median 136.70 ns with the exact bucket directory, 935.06 ns with branch extraction and packed classification, and 59.40 ns with already available keys and the same mask. The paired cost ratio for extraction plus classification versus the directory was 6.852. The directory/packed-key ratio was 2.290. Each method counts all 71 positives. This fixture repeatedly scans known fiber members with warm tables; the precomputed-key timing excludes generating, transporting and validating the keys. Build torus7-build.rs with the preceding native flags. Run branch-cost SEED ORDER, using seeds 1–24 and the six permutations of xgk four times. PCC-20261123-0c5096 records the timings. [pcc:unverified]

### Tensor-train ranks of the seven branch labels

For each subset of branch bits, place its assignments on rows and the complementary assignments on columns. The entry is the certified base-or-twist label. Over GF(2), all seven one-bit cuts have rank 2, all 21 two-bit cuts have rank 4 and all 35 three-bit cuts have rank 8. Transposition covers the larger subsets. TensorCuts.lean binds the packed rows to the label mask and checks right inverses over GF(2) for all cuts with at most three row bits. It proves that any matrix factorization through a bond of width w at one of these cuts requires w at least the number of rows.

In an exact binary tensor train the contraction at a cut factors its unfolding through the bond. Consequently every one of the 5,040 orders requires bond dimensions at least 1,2,4,8,8,4,2,1, counting the two endpoints. These dimensions yield 296 binary entries in ordinary dense cores, compared with 128 bits in the direct table. The entry count includes structured cores that could be implicit. The rank result rules out lossless low-bond compression of this mask over GF(2); sparse or differently encoded networks require separate analysis.

branch_tensor.py reproduces the ranks by binary elimination and checks an AND function as a rank-one control. It also computes the fewest individual table entries that can be flipped to reduce a single 8-by-16 cut below rank eight. A nonempty XOR of rows must vanish, and its current Hamming weight is both a lower bound and attainable by editing one participating row. Two cuts require one edit, 13 require two, 19 require three and one requires four. This is a single-cut sensitivity calculation with unconstrained edits. It does not establish an approximate train across all cuts.

### One timer from trace selection through the last membership scan

The trace-batches entry point reconstructs the Torus7 fiber, checks all 128 roots, lifts and orders its 71 curve points, checks the coordinates before passing them to the point API, prepares the lookup and point-addition state, scans all 142 outputs of each batch, then drops working storage. Generation returns both coordinates, so point lifting is charged once. The original build uses 663fc4fb5 arithmetic, scalar lifting and sorted lookup. The specialized build uses a82976381 arithmetic, eight-lane lifting, signed-pair addition and exact bucket lookup. Both use the same recurrence generator. Before timing, each build verifies its complete ordered table against lifts of the digest-matched archived keys. The scalar oracle checks each panel's full hit count.

| Batches | Random median paired speedup | Positive mix median paired speedup | Original positive mix µs | Specialized positive mix µs | Matches in positive mix |
|---:|---:|---:|---:|---:|---:|
| 0 | 2.984 | 2.983 | 10.60 | 3.59 | 0 |
| 1 | 2.892 | 2.879 | 12.03 | 4.18 | 2 |
| 4 | 2.629 | 2.606 | 15.64 | 5.96 | 2 |
| 16 | 2.268 | 2.288 | 29.92 | 13.00 | 4 |
| 64 | 2.072 | 2.085 | 87.27 | 41.86 | 16 |
| 256 | 1.948 | 1.982 | 316.51 | 158.89 | 64 |

The specialized build was faster at each workload and input mix in all 24 paired rounds. Timings are wall time per invocation on the M4 Pro. Compile the common rust-batch-width.rs harness with the two field revisions and flags specified in the original-anchor comparison. Pass trace-batches, the reconstructed key file (for checking and fixture preparation), and seeds 133–156. Build order alternates by seed. Repeated invocations rebuild their state while reusing warm code and allocator caches. Input generation, process startup, relation production, and the rest of the solver are outside this interval. PCC-20261123-74b74c records the measurement. [pcc:unverified]

### Native NEON square-root chain

The arm64 prototype computes four canonical M31 squares per vector. SQDMULH gives the high half of the doubled signed product, equal to the square divided by 2³¹ with downward rounding. Ordinary word multiplication supplies the low 31 bits. Add the two parts and select the unsigned minimum of the sum and its wrapping difference with p. WordReduction.lean proves the no-saturation bound, high/low reduction identity, and wrapping minimum rule. Disassembly of the native M4 Pro binary contained sqdmulh.4s. The native control checks 32,768 lane results after all 29 squarings against scalar u64 remainder arithmetic, including repeated boundaries. Each timed table variant also checks all 71 coordinates against the scalar lift before timing.

Thirty screening rounds tested one, two, four and eight independent 128-bit vectors. A separate 36-round comparison ran all six orders of portable width 8, portable width 32 and NEON width 32. Median times for complete tables were 3.280, 3.155 and 2.498 µs, respectively. Median paired ratios were 1.314 against width 8 and 1.271 against width 32. The native path won 35 of 36 comparisons against each control. The matched-width interquartile range was 1.228–1.307.

With the signed-pair arithmetic and lookup held fixed, the positive trace-to-scan panel measured portable width 8 / NEON width 32 median paired ratios of 1.286, 1.230, 1.149, 1.039, 1.008 and 0.987 at 0, 1, 4, 16, 64 and 256 batches per table. At 256 batches the median times were 158.17 and 160.74 µs. The observed benefit concentrates in workloads that rebuild the table frequently. The explicit mode remains selectable in the benchmark.

Compile torus7-build.rs with the preceding native flags. The validate-neon mode checks field arithmetic. Codes 104, 108, 116 and 132 select native widths 4, 8, 16 and 32. For the trace comparison compile the common harness twice with --cfg signed_pairs, enabling --cfg neon_coordinates only for the native arm. Use seeds 157 through 180, alternating build order. PCC-20261123-038476 records the local measurements. [pcc:unverified]

### Explicit NEON in repeated signed-pair batches

The optional arm64 path packs 71 ordinary denominators and one padding word. A zero contributes one to the lane product. Four or eight product lanes share a scalar field inversion, then a vector reverse pass recovers the ordinary reciprocals. A further option computes both slopes and both affine coordinates in four-wide vectors, with scalar exceptional addition on matching abscissas. The oracle in signed-pairs mode checks every point, including equal-abscissa inputs and the identity. WordReduction.lean verifies doubled-high multiplication for arbitrary canonical operands, the 32-bit fold bound and the unsigned modular subtraction rule.

On the Apple M4 Pro the initial 24-round denominator-only panel measured scalar/vector ratios of 0.958 for four lanes and 0.997 for eight. A three-arm screen with the vector affine finish gave 1.004 for the full variant, with 12 wins in 24. A longer comparison on 16 new seeds measured median 648.41 ns for the scalar specialized path and 611.10 ns for the full vector variant per 142-point batch, paired ratio 1.054 and 15 wins. With table generation included, 24 fresh positive-control rounds gave ratios of 0.990 at one batch and 1.010 at 256 (15 wins at 256). At 256 random batches the ratio was 1.013 with 14 wins. All trace trials used the same eight-lane portable coordinate generator and counted full scans. The scalar signed-pair path remains the default.

Compile the common harness with a82976381 field.rs, native flags and --cfg signed_pairs. Enable --cfg neon_products for four lanes, add --cfg neon_eight for eight, and add --cfg neon_finish for the packed affine finish. The first two panels use the six possible build orders four times with seeds 181–204 and 205–228, respectively. The longer confirmation alternates scalar/full order over seeds 229–244 with 4,096 repetitions. The trace-batches comparison alternates build order over seeds 245–268. PCC-20261123-954bfd records local timings. [pcc:unverified]

### What smoothness predicts in the Torus7 fiber

A trace coordinate x represents z through x = z + z⁻¹. Applying g(x) = x²−2 doubles the exponent of z. TorusOrder.lean proves that reaching −2 after n steps gives z exact order 2^(n+1) in any field of characteristic different from two. It also checks the archived terminal 340921998 reaches −2 after 23 more steps and specializes the result to the entire seven-step fiber. Hence every represented element has the same power-of-two order, including the elements behind all 71 base labels and all 57 twist labels.

For integer smoothness, torus7-smooth.gp factors each canonical representative x between 0 and p−1. The panel uses the traces of powers 1,3,…,63 of the original torus element as seeds and applies g seven times to obtain 32 distinct terminals. All 4,096 roots passed the 30-step order test. A separate Python replay reconstructed each fiber by successive square roots and verified every count by trial division through the largest prime at each bound.

| Largest allowed prime factor | Base lifts among smooth x, original fiber | Base lifts among smooth x, 31 other fibers | Base lifts among remaining x, 31 other fibers |
|---:|---:|---:|---:|
| 256 | 1/2 | 9/29 | 1983/3939 |
| 1024 | 3/8 | 88/190 | 1904/3778 |
| 4096 | 7/16 | 246/517 | 1746/3451 |

None of the three bounds enriched base lifts on the additional fibers. The deterministic panel measures lift frequency. It supplies no relation-yield or runtime estimate. Run gp -fq torus7-smooth.gp to reproduce the per-fiber counts. PCC-20261123-e7071a records the census. [pcc:unverified]

### Reuse of branch labels across 32 Torus7 fibers

fiber_masks.py reconstructs the roots for the previously selected odd-power terminals and computes the 128-bit base-point label mask for each one. A second calculation using PARI polynomial roots and quadratic characters reproduced every terminal and mask. The archived mask makes 1,965 errors on the 3,968 coordinates of the other fibers. A per-key majority fitted on the first 16 fibers makes 1,026 errors on the last 2,048 coordinates (ties predict twist). These are deterministic panel comparisons.

FiberMaskReuse.lean reads fiber-masks.csv and proves that every branch key occurs with both labels. Any classifier that sees only the key makes at least 1,761 errors on the 4,096 equally weighted records. Per-key majority attains this bound. Any filter shared across the whole panel that must keep every base label must admit all 128 keys.

Terminal identity allows a smaller, one-sided filter. Pair each fiber in the first half with one from the second half and store the union of each pair's positive masks. The weight of a pairing edge counts keys that both fibers can reject. An optimal bipartite matching has total weight 574, rejecting 1,148 records across the paired fibers. All 2,063 base records pass, along with 885 of the 2,033 twist records. Pairing by the same position in each half rejects 1,008 records. Lean checks the attaining assignment, all 256 edge-price inequalities and the matching upper bound; a subset dynamic program independently reproduces the optimum. The 16 masks occupy 256 bytes before routing metadata. Exact classification of survivors needs further work. This count gives the best safe rejection rate for this specific pairing constraint, assuming the branch key and fiber identity are available. No timing is inferred.

### Timing cached label masks on known fibers

The fiber-filter mode takes a permutation seed and method order. Each method lifts a panel of 4,096 abscissas on 32 fixed fibers, checks the ordered output against scalar lifting and then times 128 repetitions. The direct path and both filters use the same portable eight-lane ordinate kernel. The filtered arms include mask lookup, survivor compaction, tail padding, checking the ordinates and writing the points. Input preparation, building the masks and allocating reusable output storage precede timing.

The Apple M4 Pro screen used seeds 1–30. With keys supplied, the direct, paired and exact medians were 54.62, 39.96 and 28.70 µs per panel. Deriving keys inside the timed loop raised the paired and exact medians to 66.54 and 54.17 µs. The first three-method confirmation (seeds 31–54) overlapped a Lean replay and had higher absolute times. After replay finished, all six orders ran four times on seeds 55–78. Direct, paired and exact medians were 54.10, 39.95 and 28.27 µs. Paired and exact each beat direct in all 24 rounds. The median within-round ratios were 1.352 and 1.912. Every arm returned the same 2,063 canonical points. These observations concern repeated lifting on these known fibers with precomputed masks. Initial mask construction and a comparison to the wider NEON lift are outside this measurement. PCC-20261123-53df79 [pcc:unverified]

### Generate roots in branch-key order

At each inverse step, place the lower root in slot 2i and the higher root in 2i+1. The leaf index then gives its seven-bit branch key directly. FiberAddress.lean proves the address identity for any bounded binary tree satisfying the parent and sign laws on its reached edges. The Rust oracle separately checks all 4,096 leaf addresses, terminal identities and mask bits against independently evaluated functions and scalar lifting. When both bits for a final sibling pair are clear, generation may skip its square root. This removes 501 of the 2,048 final forks across the fixed panel.

On Apple M4 Pro, the direct generator and eight-lane lift took a median 269.76 µs per panel. Changing only the root order took 274.82 µs. Using the exact mask to select slots took 243.39 µs. Skipping empty final forks as well took 221.51 µs, a median within-round ratio of 1.227 against direct and 48 wins in 48 rounds. Each arm generated roots from the terminals, wrote points and sorted the output by fiber. All returned the same 2,063 points. Mask construction remains outside timing. The workload models regenerating points from known terminals where 512 bytes of exact masks are available. It does not measure cold mask discovery, cached-point retrieval, a tuned vector inverse-tree comparator or a collector run.

Reproduce using the native torus7-build.rs build above and the fiber-address mode with a terminal rotation and method order. Codes d, a, e and s select the four arms in report order. Rotations 0–23 use the permutations of daes in input enumeration order and rotations 24–47 reverse that schedule. Each timing averages 32 panels. PCC-20261123-be7ea0 [pcc:unverified]

### Cold generation from 32 terminal coordinates

The fiber-cache benchmark charges the first build and resets retained state between campaigns. Within a campaign each request materializes the same sequence in caller-provided output storage, sorted separately by fiber. Only the terminal column of the archived input is read. The mask arm constructs its 512 bytes of membership data while producing the first output. The point-cache arms copy that output into a newly allocated vector and copy from it on subsequent requests (33,008 bytes of point payload). All arms exclude parsing the terminals and allocating caller storage.

Starting from an arbitrary terminal in this panel, seven successive inverse steps give one leaf. Its 24th forward iterate supplies the step trace for the single-fiber recurrence already used by roots(). One further square root supplies a neighboring trace. A second-order linear recurrence then expands the full fiber. Each of the 32 sorted coordinate arrays exactly matched the inverse-tree oracle, including coordinates that do not lift. Each benchmark arm also compared its full output to scalar lifting on every request before timing. FiberRecurrence.lean proves the trace recurrence identity and preservation of the terminal power under multiplication by a period root of unity. The selection of the seed and neighbor and exhaustive coverage on this panel are checked by the native oracle.

Median campaign times in µs on Apple M4 Pro:

| Requests | Tree | Tree with mask reuse | Tree with point reuse | Recurrence | Recurrence + NEON | Recurrence + NEON with point reuse |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 274.65 | 273.61 | 272.84 | 95.82 | 61.82 | 63.20 |
| 2 | 543.89 | 500.36 | 275.96 | 188.92 | 122.19 | 63.64 |
| 4 | 1093.73 | 937.96 | 279.33 | 372.75 | 248.15 | 64.30 |
| 8 | 2188.40 | 1831.87 | 278.14 | 755.37 | 499.18 | 65.76 |

The one-request paired ratios against the inverse tree were 2.860 for recurrence with the identical eight-lane lift and 4.462 with the existing NEON lift. Both won all 24 comparisons. Neither needs cached labels. This generalizes the repository's existing single-fiber recurrence to this panel of supplied terminal coordinates. The control was the inverse tree used for the preceding pruning experiment. This benchmark measures point-table construction, with cold referring to algorithm state, on a warmed process.

Build torus7-build.rs with the native flags above. Mode fiber-cache takes the terminal rotation, number of requests, and method order. Codes d,m,c,r,v,C correspond to the six columns in order. The initial three-method screen used rotations 0 through 23. The six-method comparison used rotations 24 through 47, cycling initial position and reversing order on alternate groups of six. Each timing averages eight fresh campaigns. PCC-20261123-52c75f [pcc:unverified]

### Exact coverage of the trace recurrence

FiberOrbit.lean proves that for a nonzero field element z of order 2^31, the 128 traces of z raised to exponents 1 + 2^24 i are distinct. Equal traces would force equal field elements or a product of one. The exponent bounds and congruences exclude both collisions for distinct slots. All traces evaluate to the same terminal under seven iterations of x ↦ x²−2. The resulting polynomial has degree 128, so those slots exhaust its roots in the ambient field.

The theorem generated_exact applies to the second-order recurrence itself. Either sign of a square root of the initializer discriminant selects a neighboring trace, and reversing the step permutes the slots. For terminal 340921998, archived_generated_exact derives the order from the earlier TorusOrder theorem and identifies the fiber directly by that terminal coordinate. Its inputs still include a nonzero trace representative for the starting leaf and the two initializer equations. The proof covers the algebraic recurrence. Timing and the Rust arithmetic implementation have separate evidence. PCC-20261123-e9f019 [pcc:unverified]

To replay with the Lean 4.34.1 mathlib environment, enter this experiment directory under lake env, create a fresh temporary directory for compiled modules, and prepend it to LEAN_PATH. Compile FiberRecurrence.lean, TorusOrder.lean and FiberOrbit.lean in that order with lean -DwarningAsError=true and -o pointing to the corresponding module name in the temporary directory. The axiom report for M31FiberRecurrence.archived_generated_exact lists propext, Classical.choice and Quot.sound.

### From terminal coordinates to exact fiber coverage

PanelInitializer.lean reads the terminal column of fiber-masks.csv and checks the 32 distinct terminals by kernel reduction in ZMod 2147483647. It checks every inverse edge in the seven-step descent, the 23 further doublings to −2, and the discriminant and neighboring-trace equations using the generator's exponent and inverse of two.

PanelCoverage.lean proves panel_exact. For each listed terminal, run the second-order recurrence in the base field starting from the computed leaf and neighbor. Its 128 outputs, mapped into any algebraically closed extension, are distinct and exhaust the geometric roots of the seven-step doubling polynomial over that terminal. The proof constructs a nonzero trace representative in the extension, derives its order from the terminal, and applies the orbit theorem. Only membership in the archived panel is required of the supplied terminal. The proof models modular arithmetic and the recurrence. The machine-code implementation and elapsed time are assessed by separate native comparisons.

Replay in the Lean 4.34.1 mathlib environment with the procedure above, adding PanelInitializer.lean and PanelCoverage.lean after FiberOrbit.lean. Supply absolute source paths to lean so include_str can locate the adjacent CSV. Inspect M31PanelInitializer.panel_exact with #print axioms. Its dependencies are propext, Classical.choice and Quot.sound.

PCC-20261123-74a855 [pcc:unverified]

### Half-period symmetry and independent recurrence lanes

On the archived fibers, slot i+64 is the field negative of slot i. The first 64 entries therefore suffice. If a recurrence spaced by h uses coefficient s, the recurrence spaced by 2h uses s²−2. HalfOrbit.lean proves that identity for every input sequence satisfying the recurrence. For the archived and held-out steps, applying this coefficient transformation five times yields zero, giving the half-period sign change. This also justifies splitting the first half into four or eight independent residue classes after seeding the first two entries in each class.

The local Apple M4 Pro comparison starts from each terminal, constructs the full array of 128 coordinates, lifts through the same 32-wide NEON code and sorts points per fiber. All candidate arrays matched the full recurrence slot by slot. Independently generated inverse trees and scalar curve lifts matched the resulting sorted points. A second panel uses the traces of odd powers 65 through 127 of the element represented by the first archived terminal. Its 32 terminals are distinct and outside the archived panel. Preparing the terminal inputs and oracle comparisons precedes timing. Each arm rebuilds the panels 64 times per timing. Each panel runs all 24 orders twice (the second cycle reverses the sequence of orders).

| Method | Archived median µs | Holdout median µs | Paired speedup archived | Paired speedup holdout |
|---|---:|---:|---:|---:|
| Full recurrence, NEON lift | 61.02 | 61.36 | 1 | 1 |
| Half recurrence plus negation | 56.26 | 55.95 | 1.079 | 1.097 |
| Four independent lanes in first half | 53.10 | 53.37 | 1.151 | 1.145 |
| Eight independent lanes in first half | 53.24 | 52.87 | 1.149 | 1.155 |

Widths four and eight each beat the full recurrence in all 48 rounds on each panel. The measurements concern rebuilding sorted point tables on this host. To reproduce, build torus7-build.rs with the native flags above and invoke fiber-half ROTATION ORDER, adding holdout for the second panel. The method codes in table order are f,h,q,o. Rotations 0–23 enumerate permutations in input order fhqo and 24–47 traverse that list in reverse.

PCC-20261123-962b7b [pcc:unverified]

### Sharing cubic work between opposite abscissas

On y² = x³ + ax + b, the curve values at x and −x sum to 2b. The paired lift loads 16 abscissas and their 16 opposites, evaluates the first cubic for each pair and obtains the second by subtraction. Both ordinates still use the same 32-wide NEON square-root kernel and verification. The sorted output retains canonical ordinates in the original coordinate-pair format. PairedCubic.lean proves the cubic identity, lossless 31-bit field packing, the 62-bit bound, and preservation of lexicographic order by the packed integer comparison.

The first local Apple M4 Pro panel compared four methods, all using the four-lane half-period generator. Relative to a matched layout that independently evaluated both cubics, sharing them gave median paired ratios of 1.039 and 1.041 on the archived and held-out panels. Unconditionally writing candidates to a temporary array before compacting yielded archived/holdout medians of 51.96/52.10 µs, versus 51.71/51.61 µs when pushing accepted points directly.

A second comparison crossed the original and paired lifts with tuple and packed sorting. The packed sorter spends one pass encoding the accepted coordinates as (x << 31) | y, sorts unsigned 64-bit keys, then restores the ordinary coordinate tuples. All passes, root generation, lifting and output sorting are included. The four method codes in table order are q,p,s,w.

| Method | Archived median µs | Holdout median µs |
|---|---:|---:|
| Original lift, tuple sort | 54.69 | 53.48 |
| Paired lift, tuple sort | 51.82 | 52.21 |
| Original lift, packed sort | 50.75 | 50.25 |
| Paired lift, packed sort | 49.21 | 48.80 |

The combined method won all 48 matched rounds per panel against the original lift with tuple sorting. Median within-round ratios were 1.111 and 1.096. Each method checks the full ordered point output against scalar lifting over independently generated inverse trees. Use the fiber-half entry point and the preceding native flags. For paired-cubic.csv use rotations 0–47 and method permutations of qdpc. For paired-sort.csv use rotations 48–95 and permutations of qpsw. Both enumerate all 24 orders then reverse that schedule and alternate which terminal panel runs first. Rotations permute the same fixed terminals in each panel. Check the Lean module with Lean 4.34.1 and -DwarningAsError=true.

PCC-20261123-1f8f24 [pcc:unverified]

### Signed reduction in the 29-square ordinate kernel

The signed NEON method subtracts p from the low 31 bits and adds the high part of the square. Each intermediate lies between −p and p−1. Only the last square needs conversion to a canonical field word. A second method subtracts the high part from the complement of the low 31 bits and restores the sign on exit. SignedSquare.lean proves the range of the fold, absence of saturation in doubled-high squaring, congruence through the chain for either sign and canonicalization of the result. Both native implementations matched scalar remainder arithmetic after 29 squares on 131,072 lanes, including values near powers of two and field boundaries.

On Apple M4 Pro, the first matched panel gave median canonical/signed time ratios of 1.055 on the archived terminals and 1.057 on the holdout. A second panel tested all six method orders eight times. The canonical, signed and sign-reversed chain medians were 49.08, 45.72 and 46.82 µs on the archive, and 48.51, 45.78 and 46.37 µs on the holdout. Signed reduction beat canonical in 47/48 and 46/48 rounds respectively. Methods w, z and n select these three paths in the fiber-half command. Both panels include the four-lane half-period generator, shared cubic work, NEON ordinate lifting, point checks, packed sorting and output conversion.

The single option restricts a run to one terminal after rotation. It rebuilds the table from that terminal on each timed invocation, retaining caller output capacity and warmed process state. It checks each full ordered table against scalar lifting over the independent inverse tree. Each of the 64 distinct terminals ran once in each of the six orders of methods t, w and z. Method t is the inverse-tree generator with eight-lane portable lifting and tuple sort. For each terminal take the median across its six rounds, then report the median across the 32 terminals in each group. For ratios take the within-round ratio before either median.

| Method, one table | Archived median µs | Holdout median µs |
|---|---:|---:|
| Inverse tree and portable lift | 8.422 | 8.358 |
| Previous packed-point recurrence | 1.486 | 1.508 |
| Packed-point recurrence with signed squaring | 1.420 | 1.402 |

The directly measured tree/signed ratios were 5.867 and 5.962. The previous packed-point implementation/signed ratios were 1.057 and 1.064. All 64 terminals had a median paired ratio above one for both comparisons. Each timing averaged 64 rebuilds. These are construction measurements for one table at a time in a warmed process. They exclude process startup, choosing a terminal and downstream use of the point table.

Build torus7-build.rs with the native flags above and run validate-signed. Replay the CSV orders with fiber-half ROTATION ORDER, appending holdout for the second group and single for individual tables. For signed-single.csv the rotation is the terminal index. Replaying SignedSquare.lean under Lean 4.34.1 with warnings as errors reported only propext, Classical.choice and Quot.sound across the checked declarations.

PCC-20261123-98f990 [pcc:unverified]

### Single-table phase times and terminal square roots

The initial single-terminal profile measured root generation, lifting and packed sorting in sequence, with an external clock around 256 rebuilds. Across the archived terminals the phase medians were 665, 522 and 232 ns. The holdout medians were 663, 523 and 229 ns. The uninstrumented totals were 1,384 and 1,383 ns. This ranked root generation first. A three-method comparison replaced the eight generic power calls in the generator with 29 canonical squarings or 29 signed squarings per call. Median full-table times for generic, canonical and signed powering were 1,386, 1,293 and 1,239 ns on archived terminals and 1,377, 1,290 and 1,237 ns on holdout terminals. All arms kept the same signed NEON ordinate lift and packed sort.

A separate eight-round comparison used four methods on each terminal. P and U use generic powering, D and E use fixed signed powering. P and D include phase clocks. U and E measure just the outer loop. The order rotates through PUDE and its reverse, balancing each method across positions for each terminal. Median uninstrumented times in ns were 1,374.0 and 1,238.4 for generic and signed on the archive, and 1,379.8 and 1,233.5 on holdout. Median within-round generic/signed ratios after per-terminal aggregation were 1.115 and 1.118. Each of the 64 terminals favored signed powering on its median. Instrumented generation fell from 660.9 to 519.6 ns and from 662.8 to 521.3 ns. The outer instrumented totals exceeded the uninstrumented totals by about 51–62 ns. Clock reads also perturb the measured phases, and separately aggregated phase medians need not sum to the outer median.

All runs use the local M4 Pro, a warmed process and reusable output storage. Each invocation rebuilds one sorted point table from its terminal. The generator variants check all 128 slots against the full recurrence and the point output against scalar lifting on an independent inverse tree. TerminalRoot.lean proves that the signed scalar loop with canonicalization returns the canonical residue of x raised to 2^29 for every canonical input. The signed-product bounds are in SignedSquare.lean. The phase and three-method CSV files give per-terminal method order. Replay with fiber-half TERMINAL ORDER single and append holdout for that panel. The three-method codes are z, A and B. Compile SignedSquare.lean then TerminalRoot.lean with warnings as errors in the existing mathlib 4.34.1 environment. The axiom report for terminal_root_exact lists propext, Classical.choice and Quot.sound.

PCC-20261123-0a204c [pcc:unverified]

### Shared trace coefficient and independent coordinate generation

The trace coefficient 1330526061 comes from the first archived terminal. Seven doublings of this coefficient reach 2, and five reach 0. With a valid neighboring trace it can replace the leaf-dependent coefficient on all 64 tested fibers. The order of the roots may change. For each terminal the native oracle compares the full sorted array of 128 abscissas to the previous recurrence, and compares the returned sorted points to scalar lifts over the inverse tree.

Fixing the coefficient alone removed 24 serial squarings but failed to improve the single-table time. In the first two-method screen, leaf-dependent and fixed-step archived medians were 1246 and 1270 ns, respectively (1253 and 1285 ns on holdout). In the instrumented confirmation, generation alone took 540 versus 561 ns on the archived group and 539 versus 579 ns on holdout. These measurements do not isolate a microarchitectural cause.

The fixed coefficient also permits a 256-byte, compile-time array of 64 unsigned 32-bit weights. Given the leaf a and its neighbor b, each slot from 2 to 63 is obtained from two weights as u[i] b − u[i−1] a. This removes dependencies between successive output coordinates. The upper 64 slots follow by field negation. No terminal-specific labels, roots or points are cached. FixedWeights.lean proves the weight formula for any second-order trace recurrence, the half-period sign change for this coefficient, and preservation of the terminal under seven doublings for the certified panel seeds.

| Single-table rebuild, ns | Archived | Holdout |
|---|---:|---:|
| Prior signed generator B | 1279.5 | 1273.3 |
| Shared coefficient with dependent recurrence F | 1304.2 | 1311.0 |
| Shared coefficient with independent coordinates J | 1170.3 | 1172.7 |

On the Apple M4 Pro, the median within-round B/J ratios were 1.090 and 1.087. Each of the 64 terminals favored J on its 12-round median. Lifting and sorting are charged as before. Measurements start from one terminal in a warm process and reuse caller output capacity. The coordinate construction is specialized to the measured fiber family. The timings concern table generation.

Use fiber-half TERMINAL ORDER single, appending holdout for the second group. The tables in fixed-step.csv and fixed-weights.csv give the method orders and terminal indices. The three-method comparison runs all six orders twice per terminal. In fixed-step-phases.csv D/E are instrumented/uninstrumented leaf-dependent controls and G/H use the shared coefficient with the dependent recurrence.

PCC-20261123-3836ed [pcc:unverified]

### Fusing the two products in a weighted coordinate

The weighted generator computes u b − v a in M31. One candidate combines the two products in a signed 64-bit word and folds the signed difference twice. Another centers each operand in [−1073741823,1073741823] and adds p·2^30 to the product difference. The biased value is nonnegative and below p², so a single high/low fold followed by one conditional subtraction produces a canonical word. The centered coefficient array contains 64 signed 32-bit words computed at compile time. FusedWeights.lean proves the biased bound and the canonical residue for every choice of four canonical operands.

The initial single-terminal experiment compared J (separately reduced products), K (two signed folds) and L (center operands in the loop) in all six orders twice per terminal. Within-round median J/K ratios were 0.997 on the archive and 0.994 on holdout. J/L gave 1.004 and 1.002. A second comparison precomputed the centered weights and timed 256 rebuilds per invocation. Methods 1/2 use separate products and 3/4 use the centered table. Methods 1 and 3 have phase clocks. For each terminal, eight rounds rotated and reversed the order of all four methods.

| Median ns per single table | Archived separate | Archived centered | Holdout separate | Holdout centered |
|---|---:|---:|---:|---:|
| Generation, instrumented | 435.2 | 412.4 | 433.2 | 412.3 |
| Lifting, instrumented | 519.0 | 524.4 | 517.5 | 526.0 |
| Sorting, instrumented | 210.8 | 212.8 | 208.2 | 209.5 |
| Full build, clocks disabled | 1133.1 | 1129.6 | 1136.6 | 1128.5 |

Median paired uninstrumented ratios were 1.010 and 1.009. The centered version won on the median of 24/32 archived and 26/32 held-out terminals. The stage measurements support a modest generation saving on this machine. The change in total time is small. All candidate coordinate arrays matched the separate-product baseline slot by slot and each full table matched the scalar oracle. Use the fiber-half command with single and optional holdout as above. The CSV files record every method order. Build FusedWeights.lean with Lean 4.34.1 and warnings as errors.

PCC-20261123-4435b4 [pcc:unverified]

### Direct packed lifting on a fresh 32-terminal panel

The direct path writes each accepted canonical point as one unsigned 62-bit key, sorts the initialized prefix and expands it once into caller storage. It shares the centered-weight root generator, signed NEON square-root chain and final point representation with the preceding packed-sort control. Width changes affect register scheduling and the order of keys presented to the sorter. PackedTraversal.lean checks that the modeled traversal at each tested width visits all 128 slots exactly once and proves that the point encoding has no aliases for canonical ordinates.

In the first single-table screen, methods M,N,O,Q,R,S are respectively the previous centered-weight control, direct packed output at 8, 16, 4 or 32 four-lane vectors, and an unconditional-store variant at 8 vectors. Each terminal saw all six positions twice. Median paired M/O ratios were 1.045 on the archived group and 1.046 on holdout. At the original eight-vector width the corresponding M/N ratios were 1.012 and 1.008. Four vectors were slower on every terminal median. Wider batches and direct packing together produced the observed improvement.

A third group used the traces of odd powers 129 through 191 of the element represented by the first archived terminal. The harness verifies its 32 terminal coordinates are distinct from one another and both earlier panels. The group was first timed after the six-method screen. Every fresh terminal ran all 24 orders of four methods. Each timing averages 64 complete rebuilds from the terminal in a warmed process with caller capacity retained. Sorting, point materialization and output consumption are included. The harness compares every method's sorted points against scalar lifting over an independent inverse tree and checks generator arrays separately.

| One sorted table on fresh terminals | Median ns | Median paired inverse-tree/method |
|---|---:|---:|
| Inverse tree with portable lifting (t) | 8249.7 | 1 |
| Previous centered-weight packed-sort control (M) | 1131.2 | 7.230 |
| Direct output, 16 vectors (O) | 1081.5 | 7.566 |
| Direct output, 32 vectors (R) | 1087.4 | 7.506 |

The paired control/O ratio was 1.040 with 31/32 terminal medians favoring O; control/R was 1.038 with 30/32 favoring R. All ratios are medians of per-terminal median within-round ratios. Process startup, input selection and downstream table use are outside the timed rebuild. Raw order and timing records are in packed-lift.csv and packed-lift-fresh.csv. Use fiber-half TERMINAL ORDER single with no further argument for archive, holdout for the second panel or fresh for the third. Replay PairedCubic.lean then PackedTraversal.lean in Lean 4.34.1 with warnings treated as errors.

PCC-20261124-547bf5 [pcc:unverified]

### Canonical ordinates and the sorted packed table

FiberLift.lean proves the square acceptance criterion for every field element, including zero. CanonicalLift.lean uses that theorem to characterize the emitted ordinate. For any field value r, the lift emits y exactly when y² = r and the ordinary residue of y is at most 1073741823. Taking the smaller of the two opposite representatives implements this choice. The signed 29-step arithmetic model from TerminalRoot.lean yields the same field candidate as the exponent in the acceptance test.

For any list of M31 abscissas and any curve-value function, word_spec characterizes membership of an arbitrary integer key in the sorted output. It must encode an input abscissa and its canonical ordinate, and each such pair contributes its key. With distinct input abscissas, sorted_keys also proves that the table has no duplicate keys. Reordering the 128 inputs using any of the four measured vector widths gives exactly the same sorted list, including multiplicities if inputs repeat. The proofs apply to the mathematical filter, packing and sorting model. The native scalar-oracle comparisons check the implementations separately.

Replay CanonicalLift.lean in the Lean 4.34.1 mathlib environment with warnings as errors. Its experiment dependencies, in build order, are FiberLift.lean, SignedSquare.lean, TerminalRoot.lean, PairedCubic.lean and PackedTraversal.lean. Use the same module output directory on LEAN_PATH. The axiom report for the key membership and traversal equality theorems lists propext, Classical.choice and Quot.sound.

The native validate-packed mode additionally tests five actual packed implementations against independent u64 remainder arithmetic over 256 deterministic panels (32,768 slots). The cases include repeated abscissas, a completely rejected panel, completely accepted panels, y = 0, the half-field ordinate boundary, and appending after existing output. The oracle retained 16,664 points including 128 zero ordinates. All five implementations reproduced the scalar sequence exactly.

PCC-20261124-eb70be [pcc:unverified]

### Exact fixed-weight fibers and packed tables

FixedOrbitExact.lean proves that the fixed-coefficient recurrence visits 128 distinct abscissas whenever its seed pair satisfies a²+b²+s²−a·b·s−4 = 0 and the seventh doubling of a differs from both 2 and −2. The theorem applies to arbitrary seeds in M31 satisfying these conditions. For a collision at a positive separation k<128, shift the seed to the earlier slot. The weight identity then gives u b = q a for two constants determined by k. Eliminating b from the seed equation determines a². A 127-entry kernel check establishes that the denominator is nonzero and that a collision would force the shifted terminal to be 2 or −2. Terminal preservation transfers that obstruction to the original seed. All 128 distinct slots satisfy the terminal equation, whose polynomial has degree 128. Hence they exhaust its M31 roots.

FixedTableExact.lean checks the initializer and exclusion of the two exceptional terminals for all 96 distinct archived, held-out and fresh terminal coordinates. It checks the fresh terminal list against the same odd powers 129,131,…,191 used by the Rust harness. The coordinate formula uses the first 64 weighted positions and fills the other 64 by negation. The packed_panel theorem proves that these coordinates and the resulting sorted table have no duplicates. A packed (x,y) belongs to the modeled output exactly when x doubles seven times to the supplied terminal, y² equals the supplied curve-value function at x, and the canonical residue of y lies in the lower half of M31. This specification allows the curve-value function used by the benchmark and other M31 curves. Runtime and native-code correctness checks have separate records.

Compile FixedOrbitExact.lean after FixedWeights.lean, and FixedTableExact.lean after FixedOrbitExact.lean and CanonicalLift.lean, in the experiment's Lean 4.34.1 environment with warnings treated as errors.

PCC-20261124-d27faa [pcc:unverified]

### Two sorted tables from a shared base/twist lift

For the base equation y²=x³+2x+14, the twist equation y²=x³+2x−14 has the opposite right-hand side at −x. The earlier FiberLift.lean result established that the square of the M31 candidate equals either the right-hand side or its negative. DualPacked.lean connects that result to the canonical ordinate and to the routing rule in the packed implementation. Each shared chain produces both candidate outputs. A base match emits (x,y); a failed base check emits (−x,y) into the twist table; a zero right-hand side emits both. Each output uses its own packed keys and sort. For an input list closed under negation up to permutation, the routed twist keys sort to the same sequence as direct twist lifting.

The local Apple M4 Pro comparison builds both sorted point tables from one terminal. Method i generates the coordinates once and calls the established 16-vector packed lift separately for each curve. Method j shares the signed square chain and conditionally appends to each packed buffer. Method k uses unconditional scratch writes and conditional index increments. All three include coordinate generation, sorting, unpacking and reading the output slices. They reuse caller capacity in a warmed process. Each terminal ran all six orders twice, with 256 complete two-table builds per timing.

| Group of 32 terminals | Separate lifts, ns | Shared conditional lift, ns | Shared unconditional stores, ns | Paired i/j ratio |
|---|---:|---:|---:|---:|
| Archived | 1842.2 | 1327.0 | 1366.7 | 1.380 |
| Holdout | 1837.0 | 1331.5 | 1374.0 | 1.377 |
| Third panel | 1848.5 | 1334.2 | 1369.2 | 1.385 |

Every terminal favored method j over i on its median within-round ratio. Each of the 96 complete table pairs matched scalar lifts over an independently generated inverse tree. Across each group the base/twist point totals were 2063/2033, 2059/2037 and 2002/2094. Separate validation with repeated x, zero right-hand sides, fully accepted/rejected panels and preexisting output checked both native sharing variants on 32,768 slots. This measures the two-output workload when both tables are requested. Use fiber-half TERMINAL ORDER single and the existing holdout or fresh selector as appropriate. Replay the Lean module after CanonicalLift.lean. The validation entry point is validate-packed.

PCC-20261124-447636 [pcc:unverified]

### Sorting the 64 sign pairs once

The measured fibers contain 64 distinct nonzero sign pairs. The builder sorts their lower representatives, computes ordinates in sign pairs and visits the upper representatives in reverse. The output pass filters into both tables in increasing coordinate order. These entry points assume the measured fiber family. Method j retains the previous two packed output sorts, v sorts the lower representatives with the library sorter, and u sorts them with a fixed 21-stage bitonic network.

Each timing covers 256 complete two-table builds on the local M4 Pro in a warmed process. The first comparison ran all six orders per terminal. The repeat ran only j and u in alternating orders and reversed the terminal sequence. The speedups are medians across terminals of the median within-round j/u ratio. Reproduce an individual measurement with the existing native build flags and `fiber-half INDEX jvu single`, appending `holdout` or `fresh` for those groups. Both sorted tables are checked against scalar lifts after each method's timing loop.

| 32-terminal group | j, ns | v, ns | u, ns | Paired j/u | Repeat j/u |
|---|---:|---:|---:|---:|---:|
| Archived | 1342.4 | 1317.3 | 1273.4 | 1.048 | 1.045 |
| Holdout | 1341.6 | 1312.2 | 1280.1 | 1.050 | 1.052 |
| Fresh | 1341.8 | 1321.9 | 1283.7 | 1.049 | 1.047 |

MirrorOrder.lean proves the ordering of the expanded sign pairs. CompareExchange.lean proves multiset preservation for any sequence of modeled exchanges and the threshold law for a min/max comparator. Run `python3 extract-network.py` to regenerate NetworkBits.lean from the stage calls in packed-lift.rs. Lean checks that the resulting Boolean network sorts every 64-bit threshold mask. The extraction models the loop indices and directions. Translation from compiled Rust instructions and the SIMD routing buffers is outside the mechanized proof. Replay the three independent modules with Lean 4.34.1 and warnings treated as errors. The CSV files retain all observations, including terminals on which the candidate lost.

The axiom report for the Boolean theorem includes the native certificate-checker axiom generated by bv_decide. The permutation, threshold-gate and mirror-order theorems replayed with propext and Quot.sound.

PCC-20261124-d3ea4a [pcc:unverified]

### Emitting the two public tables from acceptance masks

Method x retains the sorted sign pairs and shared root computation from u. It assembles four lane flags at a time into separate base and twist masks, reverses the upper mask, and visits the accepted indices with trailing-zero count and lowest-bit clearing. Method y measures a separate unconditional-store variant. Each measured unit builds both tables from its terminal with reusable output capacity on the local M4 Pro.

| Workload | Group | Initial paired u/x | Publication replay u/x |
|---|---|---:|---:|
| One terminal repeated | Archive | 1.052 | 1.053 |
| One terminal repeated | Holdout | 1.054 | 1.046 |
| One terminal repeated | Fresh | 1.051 | 1.046 |
| Changing terminal | Archive | 1.171 | 1.175 |
| Changing terminal | Holdout | 1.185 | 1.179 |
| Changing terminal | Fresh | 1.179 | 1.167 |
| Changing terminal, different traversal | Fourth | 1.178 | 1.170 |

In single mode each measurement rebuilds the same table pair 256 times. Each terminal receives all six method orders. The ratio shown is the median across terminals of the median paired ratio across rounds. In stream mode each measurement builds 256 pairs by visiting all 32 terminals eight times. Each round rotates the terminal list, and pass t visits index (13i+7t) mod 32. The fourth group uses odd trace powers 193 through 255, a disjointness check against preceding groups, index (19i+11t) mod 32, and alternating two-method orders. The stream and fourth ratios summarize 48 paired rounds. The fourth candidate won 47 rounds initially and 48 on replay. These repeated local measurements share a host. The source of the workload-dependent timing difference remains unresolved.

After compiling torus7-build.rs with the preceding native flags, run `python3 replay-mask.py ./torus7-build single`, substituting `stream` or `fourth` for the other schedules. CSV output includes every timed observation. The three mask-replay CSV files correspond to the publication source and the three earlier CSV files retain the original measurements. The earlier fourth-panel CSV uses the label fresh from its separate binary. The replay command uses fourth explicitly. Stream runs check both tables against scalar lifts for every terminal before timing each method. The validate-packed command checks the ordered variants on nonzero sign pairs, including duplicate coordinates and zero ordinates.

MaskEmit.lean proves that the enumeration returns exactly the set bits in strictly increasing order. It also checks four-lane mask insertion, bit reversal, and the upper-half index formula. Compile with Lean 4.34.1 and warnings as errors. The enumeration and insertion proofs use the native bv_decide certificate checker. Compiled NEON code and buffer routing have independent scalar-oracle coverage.

PCC-20261124-5baa60 [pcc:unverified]

### Vector arithmetic and first-call owned outputs

The four-lane evaluator uses x(x²+2) for the odd part of the cubic. Doubling the signed 32-bit product and taking its high word computes the high part at radix 2³¹ for canonical operands. Combining that word with the low 31 product bits and conditionally subtracting the M31 prime gives the field product. VectorCubic.lean proves the arithmetic bounds, reduction, factored cubic identities and horizontal flag encoding. BufferBound.lean imports MaskEmit.lean and proves that each output needs at most 128 entries. The bitvector decision procedures use native certificate checking. The proofs concern the arithmetic model and output capacity. The scalar reference checks the compiled implementation separately.

The first-table entry point returns two owned point vectors, with both allocations charged. Method direct appends each emitted point to a preallocated vector. Method fixed writes each table to a 128-entry buffer and copies its populated prefix into a new vector. Both publication arms use the same vector_tables function. The timer starts before coordinate generation and ends when both vectors have been built. Process startup, scalar-oracle checks and destruction of the returned vectors are outside the interval. Each sample runs in a fresh process.

| Build and schedule | Odd trace powers | Median paired direct/fixed | Terminals favoring fixed |
|---|---|---:|---:|
| Publication, standalone comparison | 385–447 | 0.993 | 15/32 |
| Publication, standalone comparison | 449–511 | 0.990 | 12/32 |
| Prior executable, interleaved comparison | 449–511 | 1.083 | 31/32 |
| Publication, interleaved comparison | 449–511 | 1.024 | 26/32 |

The standalone schedules ran twelve paired rounds per terminal in alternating method order. The interleaved comparison ran eight rounds per terminal, rotating the four build/method combinations through ABCD, BDAC, DCBA and CADB. Within each block A and B use the prior executable and C and D use the publication build. A and C are direct. Each ratio is the median of the 32 within-terminal median paired ratios. These records show executable-dependent first-call behavior. They do not support transferring the prototype's first-call speedup to the publication implementation.

Rebuild torus7-build.rs on arm64 with the a82976381 field source, Rust 1.93.1, edition 2021, opt-level=3 and target-cpu=native. Run replay-owned.py with the binary path and previous or fresh. Each timing is accompanied by a complete comparison after timing against scalar lifts over independently generated coordinates. The validate-packed entry point also exercises empty and full outputs, zero ordinates, duplicate coordinates and untouched buffer tails. Binary SHA-256 values in the interleaved comparison are 94765907121d21870ef14d788bd3ffd2d8409bdec8e47425ba30b9e7888a7d9f for the prior executable and 1d5e79690b10bde10585db788a1a9ecf880c912c65cb05b9fccf494b717267da for the publication build.

The trace-batches setup caller in setup-batches.rs requests one ordered 71-point base table from coordinate_source::generate. Its native width-132 route in torus7-coordinates.rs calls neon_lift::points. The two-output experiment runs through torus7-build.rs. The measured two-table interval therefore supplies no observed runtime fraction for that setup caller or for a complete index-calculus run.

PCC-20261124-716b99 [pcc:unverified]
