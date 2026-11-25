# Native coordinate bases on a fixed horizontal pair

The [protocol](NATIVE_THREE_SUM_PROTOCOL.md) and
[`native_three_sum.py`](native_three_sum.py) were committed and pushed
at `d497d6a3b` before the census. The [complete output](native_three_sum_results.json)
contains every one of the 128 random-base support counts on each
curve. The runner uses the fixed `p=1009`, `r=1069` degree-five
horizontal pair described in the protocol and checks the group order
of every enumerated rational point. [pcc:unverified]

| Eight-point base | First four `x` values | Distinct nonidentity three-sums | Exact uniform hit fraction |
| --- | --- | ---: | ---: |
| Source native | `0,1,3,4` | 96 | `96/1068` |
| Codomain native | `0,2,4,7` | 92 | `92/1068` |
| Source base transported to codomain | source selection | 96 | `96/1068` |

Transport preserves the source base's indexed sums, so the third row
follows from the [transport theorem](TRANSPORTED_RELATION_GATE.md),
not a second coordinate census. Independently choosing the low-`x`
base on the codomain lowers full-group support by four points, or
`1/24` relative to the source count. This is a point-dependent
factor-base relation-yield comparison on a fixed horizontal edge.
It does not establish a general CM penalty or performance at P-192.
[pcc:unverified]

The 128 same-size random-base controls on each curve are descriptive:

| Curve | Min / median / max support | Random arms with support at least its native base |
| --- | ---: | ---: |
| Source | `58 / 96 / 96` | `84/128` |
| Codomain | `46 / 96 / 96` | `96/128` |

The source native base reaches the observed maximum, and the codomain
native base lies below that panel's median. The pair and low-`x` rule
were known before this panel, so the arm fractions are not significance
levels. They show that the four-point difference is well within
same-size base variation in this finite control. [pcc:unverified]

An alternate check enumerated one generator's 1069 scalar labels on
each curve and recomputed all 120 unordered triple sums by adding
their labels modulo `1069`; it returned `96` and `92`. This checks the
support aggregation through a separate representation, while sharing
the runner's group law and therefore not constituting independent
verification. Reproduce the frozen output with:

```sh
python3 research/cm_joint_s4_20261123/native_three_sum.py > /tmp/native_three_sum_replay.json
cmp /tmp/native_three_sum_replay.json research/cm_joint_s4_20261123/native_three_sum_results.json
```

SHA-256 before this report was added: protocol
`b56530f506b915b4f7db7af18d4ddbb0c22aa7ec3c48640b9e71e2086e7b957f`,
runner `053fb4cc0843d023b070f9b0f4dde25a78085243a5fd73e8a93ec80f80279561`,
result `01a12ce0fa3855eaead90ea4bc822a6d181094186f14083486578aa91fd450a7`.
[pcc:unverified]

This exact yield screen rejects the fixed low-`x` codomain-native base
as a reason to run a larger coordinate-solver panel. A successor would
need a predeclared base construction with a mechanism for a larger
point-relation yield or a lower verified solve cost, and then a full
same-target accounting against rho. This result does not rule out
other native bases, isogeny edges, or coordinate systems.
[pcc:unverified]
