# N41 adjacent-union six-slot recovery

The adjacent-Frobenius union produced an unpinned six-point decomposition
of the frozen public N41 target, and reusable verified factor logs recovered
its scalar **12,172,994,855**. Independent checked-Sage replay verified the
selected point sum, every source row's column transport, the scalar group
equation, and the validation-only fixture. The ordinary-host target-dependent
join plus recovery and replay took **289.636 ms**; the separately prepared
3+3 index took **515.010 ms**.

The exact curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^41+t^3+1)`, subgroup order `549756390943`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. The public target is
`(1458168294740,1672312028033)` from the prior frozen W6 workload
`0a9ad56165ec`. The six fixed Frobenius rotations are
`0,5,10,15,20,25`. Each original slot has 64 exact subgroup points;
adding `P+tau(P)` gives 128 distinct points per slot, no overlap among
the six slots, **B=768** in their union, and the same **26** independent
factor-log columns. Every image log is `(1+lambda)` times its source log,
with `lambda=256851699273 (mod r)`. The [source census](result.json)
checked all 384 original and 384 image points on the exact curve.

| Frozen arm | Result | Left index rows | Right probes | Reusable setup | Target-dependent native join | Peak RSS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Constructed group-sum control | Verified six-point row | 2,097,152 | 1 | 519.298 ms | 0.004 ms | 69,091,328 B |
| Ordinary public target | Verified six-point row | 2,097,152 | 312,592 | 515.010 ms | 288.768 ms | 69,091,328 B |

The ordinary hit uses row IDs `[91,0,19,19,10,15]`; one selected point is
from the new image branch. The six points fold into five nonzero columns
after combining the repeated column. [Independent Sage replay](replay_result.json)
checked all 384 source orbit bindings and both selected sums.
The [factor-log recovery](recovery_result.json) checked the pre-existing 26
logs against the generator, bound every union row to those logs, summed the
ordinary relation's six coefficients, and verified `scalar*G=Q`. The
target-dependent recovery and group replay took 0.868 ms, yielding the
289.636 ms diagnostic combined interval. Input loading, source generation,
log preparation, and index setup are outside this interval, with the
index setup reported above.

The [screen protocol](protocol.json), [join protocol](join_protocol.json),
[replay protocol](replay_protocol.json), and
[recovery protocol](recovery_protocol.json) were frozen before their
respective steps and bind the sources, inputs, accepted Sage runtime,
worker count, 120-second setup and online caps, and 4-GiB RSS cap.
The planted group-sum arm checks the implementation; the public arm is the
ordinary-query evidence. This was an ordinary-host method test, without a
matched isolated same-point rho pair. `candidate_id` remains `null` until
the complete N131 source and stage policy are fixed.

The result establishes a concrete six-leaf control for the N131 ten-leaf
source proposal. The next gate is an exact branch-bit SAT encoding on this
same N41 source, including an unpinned ordinary target, followed by a
source-bound N131 ten-leaf formula cost screen and one frozen ordinary
N131 query. The N41 group join's 0.289-second online time is a measured
component on a different field, not a timing prediction for N131 SAT.
