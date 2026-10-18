# Native NTL norm removes the subset bottleneck; dense full-source norm caps

**A native `GF2EX` implementation evaluated the exact N131 W20
target-conditioned two-pair norm on 4,096 valid codes in 6.409 seconds
monitored wall, using 77,135,872 B sampled combined peak RSS.** It retained
the constructed code pair `(3,16722)` and returned a degree-zero GCD on the
paired public raw point. An independent native evaluator checked all
4,096² code pairs on both points and reproduced those outcomes. The
same dense norm with all 132,045 codes reached its 600-second wall cap
after reusable source construction and before emitting a target row;
that attempt remains `BOUNDED_UNKNOWN`.

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[u]/(u^131+u^13+u²+u+1)` with `y²+xy=x³+1`. The exact W20 source
uses seed mask 898618 and rotations 0 and 18. The constructed two-pair
point and the frozen public raw point are the two coefficient rows in
[`coefficients.tsv`](coefficients.tsv). This is a two-pair residual
component; the public raw point here is the W33 resultant control,
not the complete frozen one-target challenge point in
`fresh_target_public.json`.

| Source codes per slot | Target rows | Norm/GCD result | Monitored wall | Sampled combined peak RSS |
| ---: | --- | --- | ---: | ---: |
| 256 | constructed and public | `(3,16722)`; degree zero | 0.473 s | 45,350,912 B |
| 4,096 | constructed and public | `(3,16722)`; degree zero | 6.409 s | 77,135,872 B |
| 132,045 | both rows requested | `BOUNDED_UNKNOWN` after source vanisher | 600.081 s | 510,083,072 B |

The full-source run completed the target-independent degree-132,045
source vanisher in 9.300 seconds and emitted no target `ROW`. Its
empty stderr, intact monitoring, `WALL_CAP`, and sampled RSS are in
[`receipt_132045.json`](receipt_132045.json). The cap does not
classify either target row.

[`native_norm.cpp`](native_norm.cpp) uses NTL `GF2E/GF2EX` for the
balanced quartic product and polynomial GCD. It reconstructs the
132,045 valid codes from the independently audited support table and
checks product injectivity. The compiled binary, NTL and GMP headers
and libraries, support, field kernel, coefficient input, checked-Sage
runtime receipt, exact commands, caps and outputs are hashed in each
protocol. The wrapper was launched through the checked repository Sage
launcher. [`verify.py`](verify.py) checks all receipts and source hashes;
the [proof map](PROOF_MAP.md) identifies the inherited checked theorem
and concrete finite-field bridge.

The [blockwise continuation](../n131_w20_block_norm_20261018/RESULT.md)
replaces the single degree-528,180 dense target norm with 33 bounded
second-code blocks, preserving exact source coverage. `candidate_id`
remains null while the full relation and one-target pipeline are open.
