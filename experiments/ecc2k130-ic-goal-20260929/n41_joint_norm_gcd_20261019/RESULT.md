# Joint N41 pair-family intersection by quadratic norm and GCD

The target-conditioned norm/GCD method found the exact first-family
intersection for **eight frozen N41 pair-sum keys without enumerating the
284 first-family states during each query**. Four known-member keys gave
GCD degree one and one independently checked pair witness each. Four
public-query nonmembers gave GCD degree zero. The method also passed two
exceptional-key controls, including removal of a factor whose translated
second point has `x=0`. A nine-term linearized annihilator represents the
second-family source-product condition without its degree-142 dense point
polynomial.

## Exact construction

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u³+1)`, with `y²+xy=x³+1`, subgroup order
549,756,390,943, and cofactor four. The frozen W9 source has 284 signed
pair states in each of the first two slots, with 142 distinct
`x` coordinates per slot. The first slot uses rotation zero; the second
uses Frobenius rotation six. The [input keys](../n41_implicit_pair_oracle_20261019/keys.json)
were labeled by an exact 79,424-entry group-law census before these runs.

Precompute `f_A(X)`, the product of `X+x(A)` over the 142 distinct
first-family coordinates. For a public query key `K`, use the binary-curve
addition law to write `x(K−A)=u(X)+v(X)Y` in the coordinate ring
`Y²+XY=X³+1`, modulo `f_A`. In the dense arm, evaluate the second-family
coordinate polynomial at this element. Its norm is a univariate polynomial
in `X`; the GCD with `f_A` gives candidate first coordinates. Point
reconstruction and the exact group/column checks finish the lookup.

The sparse arm instead recovers the rotated second-family source product
from `x(K−A)`, then evaluates its nine-term linearized annihilator by eight
quadratic-algebra squarings. A zero norm supplies the same GCD candidate
set. The rotated equation avoids undoing Frobenius on every query. The
[proof map](PROOF_MAP.md) gives the checked algebraic implications and the
finite implementation bridge.

| N41 arm, same eight frozen keys | Precompute wall | Sum of eight internal query intervals | Per-key range | GCD and group result |
| --- | ---: | ---: | ---: | --- |
| Dense Horner, 142 coefficient steps | 0.327 s | 107.700 s | 8.701–26.516 s | Four degree-one members, four degree-zero nonmembers; exact witnesses |
| Dense blocked evaluation, 12-coefficient blocks | 0.606 s | 35.785 s | 2.638–5.957 s | Same results and witnesses |
| Sparse nine-term annihilator | 0.267 s | 23.866 s | 2.134–4.638 s | Same results and witnesses |
| Prior direct 284-state scan | See prior receipt | 2.549 s | 0.211–0.543 s | Same eight exact labels |

These are ordinary-host algorithmic diagnostics with separate process
runs, not a qualified CPU speedup comparison. The sparse run's raw maximum
RSS was 286,359,552 bytes; the raw OS counter and source/runtime are
retained in [sparse_result.json](sparse_result.json). The precompute and
query intervals are separated in every result. The first version reached
a JSON serialization error after its first algebraic query; its
[failure receipt](first_attempt_failure.json), hash-matched
[original source](run_joint_v1.py), and original protocol remain beside the
corrected run.

The [special first-coordinate control](special_result.json) uses a key
whose `x(K)` occurs in `f_A`. The algorithm removes that factor from the
quotient ring and checks its two curve points directly. The
[zero second-coordinate control](zero_second_result.json) creates a key
for which one translated second point has `x=0`; because this source
family has no second-slot state with `x=0`, the sparse algorithm removes
that GCD factor before inversion. Exact 79,424-entry censuses label both
controls. Each control agreed with its census.

## N131 transfer boundary

The joint norm/GCD step eliminates online first-state enumeration at N41,
but its first-family quotient ring still has degree 142. The earlier W29
N131 source projection gave about 273,235,968 signed states per slot. If
they formed two-point `x` fibers with no cross-code `x` collisions, the
corresponding dense first-family polynomial would have about 136,617,984
roots. Two dense polynomials over `GF(2^131)` would require at least
4,645,011,490 bytes of raw 17-byte coefficients, above the frozen 4-GiB
worker cap before arithmetic storage. That is a conditional size
calculation from the projection, not an exact N131 census. The sparse arm
removes the second dense polynomial, but a dense first quotient of this
projected size still has no demonstrated path through the 600-second cap.

The next algorithmic gate is a compact first-family quotient or a direct
sparse-polynomial intersection algorithm that retains the norm's exact
rejection property without building a degree-proportional first-family
array. Test it on these eight keys and both exceptional controls before
the frozen N131 ordinary public-point query. The complete single-target
online and same-point rho comparison remains downstream of that relation
gate. `candidate_id` remains `null`.

Run `python3 audit.py` to replay the [terminal audit](terminal_audit.json)
over eight frozen protocols, 43 source hashes, the three ordinary-key
arms, two exceptional controls, and three checked Lean theorems. All local
Sage runs used `/Volumes/SSD990/cryptanalysis/sage -python` and the
[runtime receipt](sage_runtime_info.json) was captured before the queries.
