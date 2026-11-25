# Frozen equal-yield mixed-base S4 component comparison

Status: frozen before the measurement output. The trigger was an
eight-query exploratory source-versus-mixed solve probe on
2026-11-25; its timing is not a result in this protocol. The
[signed-base ceiling](SIGNED_THREE_SUM_CEILING.md) established that
the source and two-source/two-endpoint bases each have 96 distinct
nonidentity three-sums on the fixed `p=1009`, `r=1069` degree-5
horizontal pair. This protocol tests whether the mixed base reduces
**S4 membership-solver cost at equal exact yield**. [pcc:unverified]

## Fixed inputs and arms

- Source: `y^2=x^3+4x+10` over `F_1009`, generator `G=E.gens()[0]`, supplied target `Q=[271]G`. The first Sage degree-5 isogeny has endpoint `y^2=x^3+888x+852`.
- Source base: the first four signed source x-orbits, `x={0,1,3,4}`.
- Mixed base: the first two signed source x-orbits and the dual-isogeny pullbacks of the first two signed endpoint x-orbits. Its source x-values are `{0,1,478,742}`. Every pulled point must map back under the forward isogeny.
- Two random-base controls: use `random.Random(20261130)` to sample four distinct signed source x-orbits until each has exact support 96 and differs from the source, mixed, and each other. Save their x-values.
- An A/A control duplicates the source base in a separate arm.
- Model controls: use scale `1` and the first two values of `random.Random(20261129).sample(range(2,1009),2)`. For each scale `u`, map `(x,y)` to `(u^2 x,u^3 y)` and `E` to `y^2=x^3+4u^4 x+10u^6`. Every arm uses the same model in a paired row.
- Query seeds `20261129` and `20261130`; each draws 32 nonidentity `R=[a]G+[b]Q`, with `a` uniform in `[0,r)` and `b` uniform in `[1,r)`. Retain draws and labels. Five interleaved Gröbner solves per `(seed,query,scale,arm)`, with a deterministic shuffled arm order. [pcc:unverified]

The runner is [mixed_equal_yield_cost.py](mixed_equal_yield_cost.py).
The code and protocol are committed and pushed before the measured
run. The raw output records all timing samples, query labels, exact
point-group truth, algebraic verdicts, base construction, and
S4-system build costs. [pcc:unverified]

## Acceptance and claim boundary

The primary component metric is, for each model scale, the sum over
all 64 queries of per-query median **process CPU** solve time. Report
wall time in the same way and total process real/user/sys. An A/A
ratio outside `[0.95,1.05]` for any scale fails timing admission.
Every algebraic verdict must equal exact point-group membership;
otherwise stop and diagnose correctness. Both principal bases and
random controls must retain exact support 96. [pcc:unverified]

Nominate a mixed-base *solver component* gain only if its CPU metric
is at most `0.90` times both source A/A arms and at most `0.90` times
the median of the two random controls **at every model scale**.
Report each seed separately as a robustness check. If only one
model or seed looks favorable, report model/query sensitivity.
This is a selected finite instance and no significance level is
claimed. Even a component gain is not a complete ECDLP gain: charge
isogeny construction, dual pullback, factor-base logs, relation
collection, rank, target descent, memory, failures, and matched rho
in a later frozen protocol. [pcc:unverified]

## Execution

```sh
/usr/bin/time -p /Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/mixed_equal_yield_cost.py --output research/cm_joint_s4_20261123/mixed_equal_yield_cost_raw.json.gz > research/cm_joint_s4_20261123/mixed_equal_yield_cost_summary.json 2> research/cm_joint_s4_20261123/mixed_equal_yield_cost_time.txt
```

The raw file is gzip-compressed only for repository artifact policy;
the JSON within contains every sample. [pcc:unverified]
