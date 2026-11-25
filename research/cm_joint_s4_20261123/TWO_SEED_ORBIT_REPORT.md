# Two-seed CM orbit: point relations and exact cost boundary

The [protocol](TWO_SEED_ORBIT_PROTOCOL.md) and
[`two_seed_orbit.py`](two_seed_orbit.py) were pushed at commit
`28fecc2a4` before the first census. The script constructs the
degree-five `D=-19` self-map through a horizontal isogeny and
codomain isomorphism, then checks every arc point against the
matched `[7]` scalar orbit. It enumerates all 364 indexed triples
for every nonzero target label `d=1,...,60`. Full per-target records
are in [`two_seed_orbit_results.json`](two_seed_orbit_results.json).
The separate [label-arithmetic replayer](two_seed_orbit_scalar_replay.py)
checks all 60 zero-sum and informative counts without elliptic-curve
operations. [pcc:unverified]

There are **216 informative indexed triples** in the 60-target
census, covering **46/60** target labels. Exactly 50 target labels
give twelve distinct base points; 42 of those 50 have an informative
triple. The frozen `d=3` target has twelve distinct base points but
zero triples. Thus the preselected target did **not** yield the
planned witness; selecting a later successful row would be a
different, exploratory presentation. [pcc:unverified]

For example, the `d=4` row has `Q=(19,17)` and the independently
checked points `(2,1)`, `(4,24)`, `(44,14)`, with public labels
`(1,0)`, `(12,0)`, `(0,12)`. Their sum is `O`, giving
`13G+12Q=O`. Since `12` is invertible modulo `61`, this recovers
`d=-13/12=4 mod 61`, and `[4]G=Q` is checked. It is an actual
coordinate-verified relation containing the target coefficient,
but it is not a held-out success on the frozen `d=3` target.
[pcc:unverified]

The CM and scalar arms have identical indexed points for every
target. Consequently their 216 informative triples and 46-target
support are exactly identical, rather than merely close in a sample.
The support is computable from the public coefficient pairs alone:
a mixed triple is zero precisely when `A+B*d=0 mod 61` with
`B!=0`. This is why the label-only replay reproduces every count.
The degree-five map supplies a geometric construction of the arc,
but it gives **no relation-yield gain** over the native `[7]` arc.
[pcc:unverified]

At this fixed size, the direct exhaustive procedure performs 364
three-point checks per supplied target. A standard unordered
pair-sum table for twelve indexed points has `12*13/2=78` entries
before its twelve target-side lookups, arc construction, failures,
or verification. The negation-aware rho reference
`sqrt(pi*61/4)` is about `6.92` group-addition equivalents; even
the 78-entry table is about `11.27` times that reference in
counted pair additions before the omitted costs. This is a
small-group cost screen, not a wall-time or P-192 transfer claim.
It rejects the explicit table method on this control, while leaving
open a genuinely cheaper coordinate oracle for a different base.
[pcc:unverified]

Reproduce the frozen census and independent replay from the
repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/two_seed_orbit.py > /tmp/two_seed_orbit_replay.json
cmp /tmp/two_seed_orbit_replay.json research/cm_joint_s4_20261123/two_seed_orbit_results.json
python3 research/cm_joint_s4_20261123/two_seed_orbit_scalar_replay.py
```

The useful remaining test is a predeclared coordinate solver on a
large, low-rank base with a matched native scalar-orbit control,
including natural-query yield, failed queries, setup, relation
verification, and a full same-target comparison against rho. The
present exact equality shows that any gain must come from the
coordinate solver or a different base-selection law, rather than
from the known-scalar CM orbit relation itself. [pcc:unverified]
