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
