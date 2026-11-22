# Rank-28 N131 mask decoding works; left-root enumeration sets the next gate

The direct source-mask decoder from the N41 iteration transfers exactly to the frozen N131 W29 field. It constructed a **rank-28** inverse for the rotated fixed-seed product map, decoded the constructed positive right mask from an S3 root, and processed **256** target-conditioned S3 root calls from **128** frozen source-valid left codes. The target-dependent S3 solve, mask inversion, and trace checks took **0.0754 s**; the surrounding panel loop, including reusable pair-root construction, took **0.0889 s**. An independent group audit reconstructed both signed pair-output roots for all 128 codes, confirmed their source and orbit rules, and replayed the positive two-pair sum. The decoder stores no right-coordinate index.

The present per-code scan remains too large for the one-worker 600-second N131 relation gate. The audited W29 sample's **68,308,992-code** full-domain projection would give **136,617,984** S3 root calls for **one** target-derived key. Scaling only the measured target-dependent S3 and decoding interval gives **40,234 s (11.18 h)**, around **67 times** the 600-second budget before searching outer five-pair choices. Including repeated pair-root construction raises that panel projection to **47,438 s (13.18 h)**. These are sample-based work projections, not a full N131 scan. The next method must reject left-code regions as units before the S3-root loop; direct decoding solves the right-index memory problem but not the left enumeration cost.

## Instance and algorithm

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)` and the curve is `y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. The W29 seed mask is `898618`; the 28 free canonical mask bits exclude seed bit 19. The two pair slots use Frobenius rotations `0` and `18`. The constructed positive uses source masks `3` and `18` in those slots. The target-conditioned input is their checked pair-sum reciprocal `41102146461667180593587951479720089085`. The 128 left masks were frozen by a fixed source-only generator after applying `Tr(w)=Tr(1/w)=0` to each endpoint of the fixed-seed pair; the positive mask is included as the first correctness control. This is a component workload with `candidate_id: null`.

For each source mask `a`, let `p=a(a+s)` in the declared field embedding. The pair-output reciprocal `z` obeys `Cz²+pz+H=0`, with `C=1+H`; `H` is the rotated half-trace constant. Given an S3 candidate reciprocal `b` for the second slot, compute `p/C=b+(H/C)/b`. Because `a↦a(a+s)` is binary-linear, its 28 basis images can be inverted by bit-pivot elimination to recover the canonical mask without a right-coordinate table. The producer checks the pair quadratic on each control root, the inversion on all 128 left masks and the positive right mask, and source trace eligibility on every decoded candidate.

## Measurement and independent replay

| Boundary | Frozen result |
| --- | ---: |
| Valid left codes / pair-output roots | 128 / 256 |
| Direct mask inverse rank | 28 |
| S3 quadratic root calls | 256 |
| Valid decoded right candidates | 1: the constructed positive mask 18 |
| Decoder setup, outside query interval | 0.0220 s |
| Target-dependent S3, decode, and trace interval | 0.0754 s |
| Whole panel evaluation including pair-root construction | 0.0889 s |
| Per-call median / 90th percentile | 0.249 / 0.351 ms |
| Producer self peak RSS | 255,606,784 B |
| Independent source and group audit | 128 orbit-distinct code pairs, 128 complete two-root sets, positive exact two-pair sum |

The per-root `query_ns` entries isolate the target-dependent S3 solve, right-mask inversion, and trace eligibility. The whole panel interval also includes pair-root construction for each frozen left code; frozen source selection and decoder-basis setup are separate. The run used one checked-Sage process on an ordinary shared host. The protocol declared a 120-second wall cap and 4-GiB RSS envelope; the process completed within those bounds and retained self peak RSS, but it did not use a process-tree watchdog. The 11.18-hour estimate applies the measured target-dependent rate to the sample-based full-domain code projection; source distribution, hardware noise, and unmeasured outer search make it a diagnostic rather than a completion-time prediction.

The independently implemented [group audit](audit_result.json) checked the exact target reciprocal from the sum of two curve pair outputs. Its [producer](result.json), [frozen protocol](protocol.json), checked [Sage runtime](sage_runtime_info.json), and [proof map](PROOF_MAP.md) retain the field, source, timing, and proof boundaries. `SourceProductLinear.lean` proves fixed-seed product additivity and its preservation under an additive Frobenius map. The quadratic coefficient decoder is proved in the prior N41 oracle module. Run `python3 verify.py` for the read-only terminal audit.
