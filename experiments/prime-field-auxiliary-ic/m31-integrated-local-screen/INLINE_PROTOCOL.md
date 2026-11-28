# First-witness inline allocation screen

Compare original release `m31-fast` SHA-256
`66eeee2c8fcc961e41eeb4f8162739888c13d6473c3d872fa7de61ca3f54c692`
with candidate release SHA-256
`941286d29f97320b8dbdf50294a4d242badfeca00bcfc5fc3c855cde1e63880e`.
The only source change is `PairIndex::Entry`: first pair witness inline,
collision witnesses in an overflow Vec. Both retain all witnesses and their
enumeration order. Use frozen public M31 Q=(988441464,1643383878), interval
base B=256,384,512,768, signed m2 index, seeds 0,1,2, 64 lanes, 4M queries
and 5s online cap. For each (B,seed), alternate process order by seed and
shuffle blocks with `random.Random(2026112734)`. Charge process wall and
parent-plus-child CPU from before launch through exit. Verify answers and
require exact certificate, query, relation and setup-pair-count equality
within each matched block. Preserve failures. This first-panel result is
exploratory on one public target; a positive result needs fresh-target
confirmation and matched rho before adoption or a crossover claim.
