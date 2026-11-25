# Result of the frozen y-normalized EDS ray screen

The [predeclared test](NORMALIZER_Y_RAY_PROTOCOL.md) evaluated
`chi_47(y([d]G)*Phi([d]G))`, oriented to equal `+1` at `G`, on every
`d=1,...,60` of `E/F_47:y²=x³+x+38`, `G=(2,1)`, `r=61`.
The exact prediction was equality to `chi_61(d)` at every label.
The first mismatch is `d=4`; agreement is **28/60**. All normalizer
ratios were nonzero, and the sign parity under negation was checked
pointwise. This rejects that exact ray-character identity on this
fixed smooth CM curve. [pcc:unverified]

The frozen protocol followed a three-label pilot. Full data, including
every point's normalizer and sign, are in
[`normalizer_y_ray_results.json`](normalizer_y_ray_results.json). Reproduce
with `normalizer_y_ray.py` under the checked Sage launcher. The raw
normalizer sign also agrees on these 60 points with the independently
constructed anti-Frobenius kernel sign; that observation prompted the
separately frozen [equivalence controls](NORMALIZER_KERNEL_EQUIVALENCE_PROTOCOL.md).
It does not rescue the failed scalar-label prediction. [pcc:unverified]
