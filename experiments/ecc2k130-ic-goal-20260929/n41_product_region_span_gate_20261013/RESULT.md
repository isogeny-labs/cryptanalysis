# Four-family regions saturate the N41 target-conditioned linear span

The exact census and independent Sage replay establish a sharp failure point
for this *linear span* screen: every ordered pair of four-family product
regions spans the 40-dimensional trace-zero hyperplane. Therefore the public
target's trace-zero value survives all 262,144 such region-pair screens. The
same conclusion holds for every larger contiguous product region. This
eliminates coarse coordinate-union screening as a useful pruning step for the
declared two-free-block W6 relaxation, while identifying where a stronger
label-aware constraint must enter.

## Instance and method

The frozen curve ID is `EC1N41Ckb1h023d9a38bbf7`; the field is
`GF(2^41)` with polynomial `t^41+t^3+1`. The public reciprocal target is
`1000731834126`, with absolute trace zero. This is a point-decomposition
stage experiment, so `candidate_id` is null. Its coordinate spaces come from
the 2,048 W6 product families of the preceding bilinear-rank experiment.
At level `f`, a region consists of `2^f` consecutive product codes and its
coordinate space is the union span of their individual output spaces.
There are `2^(11-f)` regions. For two such spaces `C,D`, the screen computes
the span of the first-order S3 columns `c²`, `d²`, and
`(tcd)²+tcd` for basis elements `c∈C,d∈D`, where `t` is the public
reciprocal target. It rejects if `t²` is outside this span. The union permits
different product labels in different coordinates, so it is a necessary
relaxation of the original point-decomposition equations.

| Free product bits | Families per region | Regions | Complete union-rank histogram | Sampled public rejects / 512 |
| ---: | ---: | ---: | --- | ---: |
| 0 | 1 | 2,048 | 6: 2,026; 7: 22 | 1 |
| 1 | 2 | 1,024 | 10: 1; 11: 1; 12: 1,000; 13: 22 | 0 |
| 2 | 4 | 512 | 19: 1; 23: 2; 24: 487; 25: 22 | 0 |
| 3 | 8 | 256 | 39: 3; 40: 253 | 0 |
| 4–11 | 16–2,048 | 128–1 | All regions rank 40 | not sampled |

The sampled pair counts at levels 0–3 use the frozen deterministic input law
in `protocol.json`. One constructed positive pair was retained at each of
those levels. The complete region-rank histograms were independently
reconstructed for all 2,048 product codes by `audit.py`. The complete
four-family pair conclusion comes from the theorem below and one separately
checked exceptional pair, not from the 512-pair sample.

## Dimension theorem and finite conclusion

Let `F=GF(2^n)`, `t∈F*`, and let `C,D` be binary-linear subspaces of
dimensions `r,s`. Write

`B_t(c,d)=(tcd)²+tcd` and `H={x∈F : Tr(x)=0}`.

**Theorem.** If `r+s>n`, then the binary span of
`{B_t(c,d):c∈C,d∈D}` equals `H`.

**Proof.** Every `B_t(c,d)` has trace zero. Let `λ` be in the trace-pairing
annihilator of all these terms. Moving the square through trace gives

`Tr(λ B_t(c,d)) = Tr((λ^(2^(n-1))+λ)tcd)`.

If `λ` is outside `GF(2)`, then
`μ=λ^(2^(n-1))+λ` is nonzero: the fixed field of the indicated Frobenius
power is `GF(2)` because `gcd(n,n-1)=1`. The nondegenerate trace pairing
would force `μtC` into the annihilator of `D`, whose dimension is `n-s`.
Multiplication by `μt` preserves dimension, contradicting `r>n-s`.
Hence the cross-span annihilator is exactly `GF(2)`, since both `0` and
`1` annihilate every Artin–Schreier term. Nondegeneracy makes the cross span
have dimension `n-1`, which is the dimension of `H`. ∎

At level 2, exactly one region has rank 19 and all others have rank at least
23. Thus 262,143 of the 262,144 ordered pairs satisfy `r+s>41`. The sole
exception is the rank-19 region paired with itself, product codes `[0,1,2,3]`.
Native elimination and independent Sage reconstruction each give cross rank
40 for that pair. At levels 3–11, even the minimum rank satisfies
`2r>41`. Because the public target has trace zero, its square is in the
cross span for every ordered pair at all levels `f≥2`; the extra square
columns cannot restore rejection.

## Execution and replay

The complete native census ran in 9.929 s with sampled combined RSS
26,017,792 bytes. The independent census replay ran in 9.052 s and used
46,645,248 bytes. The exceptional-pair native check ran in 0.247 s;
its Sage replay ran in 22.046 s with sampled combined RSS 282,607,616
bytes. All four jobs exited zero under their frozen one-worker, 120-second,
4-GiB caps, and monitoring reported no degradation. These are algorithmic
diagnostics on the local host, not isolated CPU speedup measurements.
The checked repository Sage launcher was used for both Sage jobs;
`sage_runtime_info.json` records its accepted build. Run
`python3 verify.py` to recheck every frozen source hash, raw-result hash,
status, cap, complete rank histogram, and finite conclusion. `terminal.json`
records that verification.

## Next experiment

The coordinate union loses the condition that all outputs in a candidate
decomposition belong to their declared product families. The next gate
should preserve those product labels symbolically while sharing computation
over a region. Test whether label-compatible, target-conditioned constraints
reject a whole region before explicit family-pair enumeration, and retain the
constructed positive witness and ordinary public inputs as paired controls.
