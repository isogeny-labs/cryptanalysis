# Frozen two-seed horizontal-orbit point-relation screen

## Exact candidate

On `E/F_47:y²=x³+x+38`, `r=61`, `G=(2,1)`, take the normalized
degree-five CM endomorphism `w=6+pi`, which acts as `[7]` on the
rational group. Let the supplied target be `Q=[d]G`. For each seed
`G` and `Q`, retain the signed orbit arc `±w^j(seed)` for
`j=0,1,2`. Its public coefficient label is respectively
`(±7^j,0)` or `(0,±7^j)` in `P=[a]G+[b]Q`.
The length-three arc and **all** target labels `d=1,...,60` are fixed
before running the census. The `d=3` row is the preselected concrete
target witness check. [pcc:unverified]

For each target, enumerate all `C(12+2,3)=364` unordered indexed
three-term multisets, allowing repetitions. Count a zero sum only
after checking the actual elliptic-curve point sum. For each zero
sum, calculate public `A=sum a_i` and `B=sum b_i` modulo `61`.
Call it informative iff `B!=0`; then independently check
`A+B*d=0`, compute `-A/B mod 61`, and verify its multiple of `G`
equals the supplied `Q`. Record the first informative witness,
all counts by target, and duplicate indexed points. A nonzero
`B` is essential; a within-seed identity has `A=B=0`.
[pcc:unverified]

## Attribution and cost gate

Build the orbit once through Sage's degree-five isogeny followed by
the unique selected codomain isomorphism taking its image of `G` to
`[7]G`. Build a matched native orbit by repeated scalar `[7]`
from the identical two seeds. Compare all twelve indexed points at
every target, not just aggregate counts. Therefore every indexed
three-sum and informative coefficient pair must be identical between
the CM and scalar arms; any mismatch is an implementation defect.
This test can establish the missing **two-seed point relation**, but
its yield cannot be attributed to the isogeny. [pcc:unverified]

The direct three-sum enumeration costs 364 point-sum checks per
target at this fixed size. A conventional pair-sum table for a base
of size `B=4L` uses `B(B+1)/2` entries and `B` lookups per query.
For a scaled proposal, use the [existing three-summand cost gate](README.md)
to charge base construction, pair-table memory, failures, and
natural-query yield against same-target rho. A useful successor
would have to replace this explicit table with a coordinate-based
oracle that is demonstrably cheaper **because of** the horizontal
map. An informative witness alone does not establish that.
[pcc:unverified]
