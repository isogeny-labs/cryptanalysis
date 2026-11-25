# Fixture membership throughput

Use the 32 structured_roots from the field31_s5_base0 public.json fixture, in manifest order, with one whitespace-separated x and membership bit per line. The bit is 1 when x occurs as the first coordinate of a factor_base pair. Compile membership.cpp with Apple Clang 21 using -O3 -mcpu=native -std=c++17. Pass the shuffle seed as the sole argument and feed these lines to stdin. The CSV records three local processes on an unpinned M4 Pro using seeds 0, 1 and 2. Each process includes every coordinate equally often and compares every output byte with its fixture label before timing. The table setup and input generation are outside the timing. Each value is a median of 40 timed samples of repeated batched classification after 10 warmups.

The mask was fitted by binary Gaussian elimination on the 32 augmented coordinate rows with a constant input bit. The rows have rank 31. Setting the free variable in each of the two possible ways gives two affine classifiers, one of which uses the linear mask 0x50a779d6 with zero constant. Address.lean checks the latter against the fixture.

A transfer check reused the 256 deterministic auxiliary fibers emitted by ../m31-projection-controls/sample.gp, each with 17 positive labels among 32 coordinates. Applying the frozen mask without refitting gave 4050 correct labels out of 8192 and zero exactly classified fibers.

## How often a fiber admits a fitted affine parity

Running the same 256-fiber generator through affine_null.py reproduces affine_null.json. Each augmented coordinate row contains the 31 coordinate bits and a constant bit. A labeling admits an affine parity exactly when its binary inner product with every left-kernel dependency is zero. For each fiber the script counts all weight-17 labelings satisfying those checks by dynamic programming over the number of positive positions and the XOR of their check columns. The observed fit decisions also matched a separate comparison of the ranks before and after adjoining the observed label column.

The frozen fixture has rank 31 and its sole nonzero dependency covers 16 positions. Exactly 282,861,360 of 565,722,720 weight-17 labelings admit an affine fit. Swapping the 16 dependency positions with their complement pairs each consistent labeling with an inconsistent labeling, because their two counts of positives sum to 17.

Across the 256 fibers, allowing a different affine parity on each fiber produced 162 exact fits. Uniformly reassigning 17 positive labels on each fiber gives an expected total of 161.1250105. On the 77 full-rank fibers every labeling fits. The comparison concerns in-sample interpolation with a per-fiber constant term. It measures neither out-of-sample prediction nor the time needed to obtain the labels.
