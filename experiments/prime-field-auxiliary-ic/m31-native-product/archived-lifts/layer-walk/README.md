# Layered affine expansion for the public M31 basis

The first half of the ordered auxiliary coset grows by doubling the list length. At length m, translate all points by mG in one batch and append them in their original order. A reverse prefix-product pass shares one inversion across the affine slopes. The existing reciprocal translation constructs the second half. This uses O(m) temporary storage for a layer of size m.

The Lean replay establishes the full ordered group enumeration, the field identity used in each reverse step, and the strict numerical inversion-count inequality. The Python implementation, native ordinate calculation and elapsed times are checked experimentally. Complete M31 calls at depths 8 and higher select the layered path.

The frozen reference is 150caa1b46b966e935df6e14392f2234d567d910. The replay compares ordered roots, map metadata and native lifts, independently evaluates every timed root through the rational map, and checks the archived depth-5 basis. It also checks partial limits and an M61 control.

## Local arm64 results

Long panel, 24 alternating paired blocks. Per-arm values are median wall milliseconds per public basis. Speedups are median within-block reference/candidate ratios. Wins count lower candidate wall time. Each call charges chain setup, all roots, native ordinate calculation and packing.

|Depth|Scalar ms|Layer ms|Wall ratio|CPU ratio|Wins|Chain inversions, scalar → layer|
|---:|---:|---:|---:|---:|---:|---:|
|5|0.594|0.526|0.883|0.973|11/24|82 → 82|
|8|0.945|1.244|1.123|1.081|13/24|227 → 113|
|10|1.938|1.552|1.214|1.166|19/24|638 → 144|
|12|7.563|6.051|1.260|1.206|19/24|2205 → 179|

Depth 5 runs the scalar walk in both arms and measures control variation. The two shorter panels are also retained. This panel measures public setup on a shared local host. Relation collection and same-target solve time are outside its timing interval.

Run the public comparison with Python 3 using `python3 replay.py /path/to/native-library --long` from this directory. The library must export `m31_lift32` as in the adjacent half-walk replay. For the proof, use `lake env lean -DwarningAsError=true /absolute/path/to/Layer.lean` in the mathlib Lean 4.34.1 environment.
