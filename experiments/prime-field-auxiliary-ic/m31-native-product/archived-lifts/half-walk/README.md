# Generate the second half of the public auxiliary coset by translation

On the auxiliary curve y²=x³+x, affine addition of the order-two point
(0,0) sends x to 1/x. For a complete ordered coset of length 2^s, adding
that point sends index i to i+2^(s−1). The public M31 preparation now walks
the first half, checks the midpoint by adding (0,0), and appends the field
inverses of those coordinates in order. Prefix products and one inversion
produce the entire second half. The complete distinctness, rational-map
sibling and terminal checks run on every output. Depths one and two use the
original walk because batch setup and the midpoint check save no inversions
there. Partial lists also use their existing walk.

Translation.lean verifies the affine translation formula, the additive
coset order and closure identity, and the backward batch-inversion step.
The benchmark checks complete ordered roots and every canonical point
against the previous revision, independently evaluating the map chain and
target cubic on each coordinate. At depth 5 it additionally checks the
pinned archive. Both arms charge chain construction and native lifting into
Python point lists. Imports, library loading and separate output audits
are outside the clock.

On the shared Apple M4 Pro in timings.csv, the median within-block full
basis wall ratios (old/new) were 1.079, 1.304, 1.344 and 1.316 at depths
5, 8, 10 and 12 respectively; wall wins were 9, 13, 15 and 13 of 16.
The depth-five follow-up used 32 blocks of 256 complete calls per arm.
The median paired wall ratio was 1.030 (20 wins), and the median paired
CPU ratio was 1.064 (21 wins). The initial depth-five marginal wall medians
disagree in direction with the paired ratio; both panels are retained.
The operation counts in counts.csv were measured outside the timing panel.

Build neon.so as in the parent README, then run:

```sh
python3 replay.py /path/to/neon.so
python3 replay.py /path/to/neon.so --repeat-five
python3 counts.py
```

Replay Translation.lean in the Lean 4.34.1 mathlib environment.
