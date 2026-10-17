# Bounded-direction affine cover of the selected N131 W20 source

A deterministic weight-one/two selector-direction sweep partitions all
**132,045** valid W20 pair codes into **32,192 affine quadruples, 1,391
pairs, and 495 singletons**. The **34,078 groups** are 1,066 above the
four-code counting minimum of 33,012; 128,768 codes (97.52%) lie in
quadruples. Independent scans of the frozen 524,493-row support file checked
that each code appears exactly once and every quadruple has XOR-zero corners.
The producer's archived-code grouping phase took **0.372 s** on this
ordinary host, with 37,453,824 B peak self RSS over its 0.450 s process
interval. This is target-independent source preparation and has
`candidate_id: null`.

## Construction and comparison

The selected N131 source is `EC1N131Ckb1heb5f1998f20b`, seed mask
`898618`, with 19-bit canonical selector codes after omitting the seed's
highest bit. The [protocol](protocol.json) freezes the source and an initial
coordinate-axis packing. Its [independent audit](audit_result.json) checked
all 132,045 codes once. The [version-two protocol](protocol_v2.json) then
pins that audited code list and tests all 19 unit directions plus all 171
weight-two directions. In ascending code order, the worker chooses the first
available affine square, then covers remaining codes with an available pair
or singleton. The [version-two audit](audit_result_v2.json) independently
reconstructs the codes from the source file and checks every stored group.

| Exact partition on the same W20 code source | Groups per slot | Two-slot Cartesian regions before column exclusions |
| --- | ---: | ---: |
| Fixed low-two-bit prefixes | 90,055 | 8,109,903,025 |
| Initial coordinate-axis greedy cover | 58,188 | 3,385,843,344 |
| This weight-one/two greedy cover | **34,078** | **1,161,310,084** |
| Earlier unrestricted affine cover | **33,099** | **1,095,543,801** |
| Four-code counting minimum | 33,012 | 1,089,792,144 |

The earlier [unrestricted partition](/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n131_w20_affine_rectangle_partition_20261016/RESULT.md)
has fewer groups. It used arbitrary affine directions and reported 11.429 s
of grouping after source loading on an ordinary host. This run's 0.372 s
grouping uses a previously audited code list, a different construction and
an unisolated host; those walls do not establish a paired CPU speed ratio.
The source scan and initial coordinate cover took 0.867 s in a separate
run. The bounded-direction groups use only two selector bits per quadruple,
so the same symbolic product chart applies.

The [Lean module](AffineChart.lean) proves the two-bit chart for an additive
source map and proves that the fixed-seed pair-product polynomial
`x(x+s)` is additive in characteristic two. Its `#print axioms` output is
saved in [lean.stdout](lean.stdout). The exact assumptions, source-code
bridge and audit boundaries are listed in the [proof map](PROOF_MAP.md).

## Cost boundary and next gate

The new cover reduces the number of two-slot regions by a factor of 6.98
relative to the fixed low-bit layout, but a literal visit to all
**1.161 billion** regions would still require **1.94 million visits/s** to
fit 600 seconds, before any target-conditioned polynomial work or the other
free source slots. The prior unrestricted cover sets a slightly lower
region-count baseline. This source result supplies exact, cheap affine
charts for the next experiment: on the frozen *unpinned N41 public point*,
test a target-conditioned predicate that can reject groups of several
unresolved pair sources without visiting their Cartesian product. Charge
group preparation and every failed probe; only then assess a frozen N131
ordinary relation query under one worker, 600 seconds, and 4 GiB.
