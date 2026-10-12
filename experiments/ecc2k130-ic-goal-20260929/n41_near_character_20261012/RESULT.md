# Low-weight coordinate characters show no stable source-addition bias

On the frozen N41 diagonal-pair source, none of the **20 training-selected** nonconstant weight-one or weight-two linear functionals of the coordinate-addition error showed a stable bias on an untouched 8,192-sample holdout. The strongest 4,096-sample training functional for raw `x` had signed bias **−5.13%**, then **−0.63%** on holdout and **+0.71%** on a uniform-subgroup baseline. The strongest for reciprocal `1/x` had **+4.74%** on training, then **−1.64%** on holdout and **−1.22%** on the uniform baseline. The maximum absolute holdout bias among the ten training-selected nonconstant masks in each coordinate was **2.10%** for `x` and **1.73%** for `1/x`.

This is a direct test of a possible approximate additive coordinate for early multi-list pruning. Its negative result covers the declared source law, polynomial-basis bit functionals of Hamming weight at most two, and the frozen sample sizes. It redirects this branch away from low-weight coordinate parity screens and back toward exact target-coupled source-image constraints.

## Frozen law and statistic

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`, with `y²+xy=x³+1` and odd subgroup order `549756390943`. Each of the first two rotated source slots supplies **30,952 signed diagonal-pair states**. A deterministic SHA-256 draw selects one state from each slot, rejecting a draw when the four folded factor-base columns are not distinct. For independent train and holdout laws, let these points be `P,Q`. The baseline takes independent deterministic hash-derived nonzero scalar multiples of the first slot's verified full-order point. All points and sums used in the panel are nonidentity with nonzero x coordinate.

For `u(P)=x(P)` and separately `u(P)=1/x(P)`, define the field error

`e_u(P,Q)=u(P)+u(Q)+u(P+Q)`.

For a 41-bit binary mask `m` in the declared polynomial basis, `L_m(e)` is the parity of selected coordinate bits. The signed bias estimate is `(#L_m(e)=0 − #L_m(e)=1)/n`. The [producer protocol](protocol.json) froze 4,096 source training draws, 8,192 independent source holdout draws, 8,192 uniform-subgroup draws, all **861** masks of weight one or two, one worker, a 180-second parent cap, and 4-GiB monitored process RSS. The complete [vector receipt](vectors.json) stores the selected state indices or scalar values and both error coordinates. The checked repository Sage [runtime receipt](sage_runtime_info.json) was saved before the run.

The first score list exposed a constant bit: polynomial-basis bit zero of both error coordinates was zero on all **20,480** source and baseline vectors. Masks containing that bit are constant or duplicate another tested functional on this panel. The independently frozen [second verification protocol](verification_protocol.json) excludes those 41 masks, leaving **820** nonconstant candidate masks per coordinate, then selects the top ten using training scores only. The holdout and baseline never influence mask selection.

## Measured result and uncertainty

| Coordinate and training-selected top mask | Train signed count / 4,096 | Holdout signed count / 8,192 | Uniform signed count / 8,192 |
| --- | ---: | ---: | ---: |
| `x`, bits 6 and 33 | −210 (**−5.13%**) | −52 (**−0.63%**) | +58 (**+0.71%**) |
| `1/x`, bits 26 and 37 | +194 (**+4.74%**) | −134 (**−1.64%**) | −100 (**−1.22%**) |

For one mask selected without inspecting holdout, the normal-approximation 95% half-width for a signed mean near zero at `n=8,192` is **2.17 percentage points**. For the source-minus-uniform difference it is **3.06 points**. Both top-mask holdout intervals include zero, as do their source-minus-uniform intervals. A conservative Hoeffding union bound for the 20 training-selected masks gives a family-wise 5% null threshold of about **4.04%** absolute holdout bias; the observed maximum is 2.10%. This states the sensitivity of this panel, not an exclusion of weaker or higher-degree source-specific effects.

The [producer result](result.json) retains every training score and each selected mask's holdout and uniform scores. The independently implemented [score replay](analysis.json) recomputes all 820 nonconstant training scores from the archived vectors and matches the producer. A separate checked-Sage [group replay](audit.json) reconstructs **128 train, 128 holdout, and 128 uniform** errors from the stored source indices or scalars and matches every recorded field coordinate. The producer's [run status](run_status.json) is `EXIT_0`, 28.278 s parent wall, and 282,329,088 B sampled peak process-tree RSS. The group audit's [run status](audit_run_status.json) is `EXIT_0`, 31.841 s parent wall, and 297,811,968 B sampled RSS. Local CPU times are exploratory without a host-isolation receipt; exact vector and score replay are the relevant gates.

The first plain-Python verifier stopped before writing an analysis because Python 3.9 lacks `int.bit_count`. Its [failure status](verification_failure_v1.json), [source](verify_v1.py), and [original protocol](verification_protocol_v1.json) are retained. Version two uses a Python 3.9-compatible parity calculation; the producer data and sample law were not changed.

## Search implication

The trace-like exact parity and polynomial-basis bit-zero invariant arise on both the source and uniform subgroup samples, so they do not select useful source families. The 20 holdout-tested low-weight linear forms behave like ordinary sampling noise under the frozen law. An approximate Wagner-style filter would need a reproducible bias in an additive coordinate under actual source additions before it can reduce the ten-pair search without losing valid relations. The next experiment should test a mathematically specified higher-order or target-conditioned relation only after showing a source-bound work advantage over the existing exact N41 join and an unpinned relation-preservation control. The N131 ordinary public-point gate stays at one worker, 600 seconds, and 4 GiB.
