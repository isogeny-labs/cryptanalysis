# Complete W29 census sharpens the fixed-outer search bound

**The full N131 W29 source count lowers the rigorous ordered right-two-pair
capacity ceiling to 72,059,681,407,150,336 group points, a 15.9995-fold
reduction from the earlier mask-only bound.** A method that selects just
one fixed outer three-pair proposal for each target-advice value needs
at least **72 advice bits** before its uniform-subgroup success *upper
bound* can reach one half. Eight fixed proposals per advice value still
need **69 bits**; even 20 million fixed proposals need **48 bits**. The
general counting implication and each threshold are checked in Lean
4.34.1. This result identifies the target-dependent selection burden
that the next joint point-decomposition constraint must carry.

## Exact source and coverage model

The curve is `EC1N131Ckb1heb5f1998f20b`,
`y²+xy=x³+1` over
`GF(2)[u]/(u^131+u^13+u²+u+1)`, with prime subgroup order
`680564733841876926932320129493409985129`. The fixed-seed W29
source has 28 canonical code bits and **67,109,836** endpoint-valid
codes in its complete `2^28`-code census. A separate numeric-order
pass reproduced that count. Each valid code supplies at most four
signed pair states in a Frobenius-rotated slot, hence
`S≤4·67,109,836=268,439,344`. Two right slots have at most
`M≤S²=72,059,681,407,150,336` distinct ordered sums. Collisions,
column conflicts, and subgroup projection can only tighten this
ceiling. The earlier mask-only ceiling was `2^60`.

The model gives each public target one of at most `C` advice values.
For each advice value it fixes at most `k` outer three-pair proposals,
then asks even a perfect oracle whether the residual lies in the right
two-pair sum set. The [proof map](PROOF_MAP.md) gives the finite-union
argument. For a target drawn uniformly from the declared prime
subgroup, success is bounded by `min(1,C k M/r)`. This is a capacity
bound on fixed outer proposals, including an all-negative path that
learns only yes/no completion feedback before its first hit. A joint
constraint that uses the public point to correlate still-free source
codes falls outside that premise and is the constructive direction.

| Fixed proposals `k` per advice value | Exact minimum advice bits before the upper bound permits one-half success | Uniform-target upper bound with no advice |
| ---: | ---: | ---: |
| 1 | **72** | `1.058821855201988…×10⁻²²` |
| 6 | **70** | `6.352931131211928…×10⁻²²` |
| 8 | **69** | `8.470574841615904…×10⁻²²` |
| 20,000,000 | **48** | `20,000,000 M/r` using the exact `M` and `r` above |

The `k=6` and `k=8` rows are motivated by the preceding complete
terminal scan: its 94.407-second public and 69.330-second constructed
parent intervals would fit six or eight sequential runs in 600 seconds
if those rates held on the other residuals. That is an ordinary-host
rate projection. The table's counting inequality is exact for any
declared `k`; it does not use a wall-time assumption.

## Frozen checks and next experiment

The [protocol](protocol.json) pins the independently checked full
W29 count, full-stream terminal verifier, prior subgroup-order and
mask-capacity result, script, Lean source and toolchain before the
arithmetic run. The [result](result.json) retains every integer
numerator, denominator, threshold and observed-rate projection. The
[terminal verifier](verification_result.json) recomputes the bound,
source identities, Lean audit and all threshold inequalities. Its
status is `PASS_EXACT_W29_CAPACITY_AUDIT`. This remains a
`candidate_id: null` component of the ECC2K-130 IC search.

The next solver experiment should bind the frozen N41 public target
to at least two still-free outer code families in one algebraic
constraint and count how many whole source-code regions it rejects
before enumerating partial sums. The unpinned N41 ordinary relation
is the positive control; separately frozen ordinary misses test
selectivity. Only a lossless gate with a source-bound N131
one-worker/600-second/4-GiB projection justifies a new public-point
relation run. The completed W29 terminal can then verify proposed
residuals, while relation rank, target descent, scalar replay and a
same-point rho comparison remain part of the full objective.
