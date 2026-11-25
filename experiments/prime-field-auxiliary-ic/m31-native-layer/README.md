# Native affine layer expansion in checked M31 basis preparation

The public setup builds a 32,768-root auxiliary coset and returns 195 target points whose signed x-coordinates are 211-smooth. In 40 local diagnostic calls, the median within-call time share of the Python affine layer walk was 39.89%. Reciprocal completion used 10.60%, sibling-fiber validation 20.18%, residual chain operations 4.18%, smoothness 22.42% and final native lifting 0.27%. These separately taken medians need not add to 100%.

The C routine translates an entire layer with one shared field inversion. The caller still computes stride doublings, verifies the midpoint, completes the reciprocal roots, checks the full fiber, constructs the smoothness divisor and lifts the survivors. A zero denominator returns failure before output-coordinate writes. Arithmetic uses unsigned 64-bit products of canonical M31 residues. The previous layer proof establishes the algebraic identities and ordering in ../m31-native-product/archived-lifts/layer-walk/Layer.lean.

The replay checked full chain metadata and every ordered root at depths 8, 10, 12 and 15. All 64 timed calls also matched the independent scalar reference for the 195 ordered points. In 32 alternating pairs, median wall times were 44.86 ms for the prior Python layer and 31.11 ms for C. The median paired ratio was 1.422; all 32 pairs favored C. Median CPU times were 38.02 and 25.90 ms, with a median paired ratio of 1.471. These are setup-only timings.

Build layer.c with `cc -O3 -shared -fPIC layer.c -o /tmp/m31-layer.so`. Build the lift library following ../m31-native-product/archived-lifts/README.md. Run `uv run --isolated --with sympy --python 3.13 python replay.py /absolute/path/to/lift.so /tmp/m31-layer.so`.
