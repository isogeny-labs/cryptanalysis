# N41 two-pair reciprocal output BDD census

**Result.** A reduced ordered BDD built from 200,000 distinct reciprocal x-coordinates of valid two-pair sums has 1,237,720 nodes. Equal-size uniform field and curve-valid controls have 1,423,144 and 1,422,442 nodes. The 13.0% relative reduction is measurable, but the representation still uses 6.19 nodes per observed value. Even a minimal three-32-bit-integer serialization would use 14,852,640 bytes for the nodes, versus 1,600,000 bytes for 200,000 raw 64-bit reciprocals. This bit order and representation therefore do not give a compact sampled output domain.

## Source and method

- Field: GF(2^41) with modulus `x^41+x^3+1`; curve: `y^2+xy=x^3+1`.
- Source: the frozen four-rotation signed W8 pair table at `../n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv`, SHA-256 `df367421657bf29d7c47a9bd62b26c6424993e81b98d4d1f70cb7e05f0d8b22a`. Slots 0 and 1 each contain 30,952 signed states. Their full Cartesian product has 958,026,304 ordered combinations before distinct-column filtering.
- The native sampler uses a fixed xorshift64* seed, discards combinations sharing a folded factor-base column, adds the two points, and retains the first 200,000 distinct nonzero sum x-coordinates. The output includes both source state IDs, x, and its reciprocal. It attempted 207,844 combinations: 7,808 column overlaps, 36 repeated x-coordinates, and no identity or zero-x sums. The sample is a bounded subset of the full two-pair output domain.
- The BDD uses the existing `fourpair_v2.bdd` routine: 41 coordinate bits in descending numeric order, reduced by unique `(bit,low,high)` nodes. Prefixes of the same sampled stream are compared with equal-size distinct uniform nonzero field elements and a separately seeded stream of valid curve x-reciprocals. Curve validity is tested by `Tr(x+1/x)=0` for nonzero x.
- The independent Python replay checks 64 fixed random source-state pairs, the four distinct columns, binary-curve addition, reciprocal multiplication, and the curve equation. It also checks 64 curve-control trace predicates. The source pair table has its own earlier Sage audit. This run is an algorithmic representation diagnostic on an ordinary host; the timings below are exploratory.

| Distinct outputs | Pair BDD nodes | Uniform field nodes | Uniform curve-valid nodes | Pair / curve-valid | Pair nodes/value |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25,000 | 300,645 | 313,162 | 325,515 | 0.924 | 12.03 |
| 50,000 | 501,650 | 535,129 | 550,633 | 0.911 | 10.03 |
| 100,000 | 806,345 | 890,540 | 903,310 | 0.893 | 8.06 |
| 200,000 | 1,237,720 | 1,423,144 | 1,422,442 | 0.870 | 6.19 |

At 200,000 outputs, sorted decimal gzip sizes are 1,099,384 bytes for the pair sample and 1,120,879 bytes for the curve-valid control. This is a modest distributional difference, consistent with the BDD count. The exact population BDD is not constructed, and these samples do not establish a bound on its size. Reciprocal x alone also omits the sign of y and the source witnesses needed for relation replay.

## Reproduction and evidence

Run from `/Volumes/SSD990/cryptanalysis`:

```sh
c++ -O3 -std=c++17 -o experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/sample experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/sample.cpp
experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/sample experiments/ecc2k130-ic-goal-20260929/n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/samples.tsv 200000
c++ -O3 -std=c++17 -o experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/curve_control experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/curve_control.cpp
experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/curve_control experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/curve_control.tsv 200000
python3 experiments/ecc2k130-ic-goal-20260929/n41_two_pair_bdd_compression_20261012/census.py
```

`result.json` gives the source/input SHA-256 digests, exact node counts, exploratory per-set construction times, and macOS peak resident bytes. `samples.tsv`, `curve_control.tsv`, and `census.stdout` preserve the measured inputs and output. The executable files are regenerated from the committed C++ sources.

## Decision and next falsifier

This branch does not supply the compact exact target-conditioned family constraint proposed for ECC2K-130. A useful next representation test must retain group-sum witness information while rejecting target-incompatible source families before explicit pair-output enumeration. The first small-field gate is an exact N41 positive and ordinary-query control with a measured rejection count per source family; if it only compresses the x-coordinate set or expands pair outputs, stop that variant before N131.

This is a stage diagnostic with `candidate_id: null`; no full IC candidate or single-target online comparison was measured here.
