# A frozen p73757 target is recovered through the anchored class-point pair index

The frozen public point `Q=(62849,63290)` in the order-199 subgroup has the verified relation `Q = -B₁ + B₄`, where `B_i=370P_i` are projected class points. The anchored class logs from the preceding experiment give `log_T(B₁)=163` and `log_T(B₄)=50`, hence `log_T(Q)=−163+50 ≡ 86 (mod 199)`. An independent Sage audit reconstructed the seeded target point, confirmed the pair equation, enumerated its subgroup scalar, and verified `86T=Q`.

## Frozen input and measured stages

The instance is `E:y²+y=x³−x²−10x−20` over `F_73757`, with `T=370P₀` of order 199. The input law in `inputs.json` fixed a seed, SHA-256 scalar derivation, rejection of identity or a projected class point, and a counter cap before fixture construction. Counter zero produced the retained public target. The target producer read `public-target.json`; `fixture.json` retained the construction scalar for the independent audit. There was no replacement after inspecting the pair-index outcome.

The target-independent stage loaded the hash-pinned 40 anchored class logs and projected the class points. They yield 36 distinct subgroup points. It indexed all `i<j` pairs with two independent signs, enumerating 3,120 signed patterns. The resulting map contains 199 distinct points, covering the entire order-199 subgroup. The first canonical witness for the public point is `(i=1, sign=−1, j=4, sign=+1)`.

| Local stage | Observed time | Boundary |
| --- | ---: | --- |
| Base projection and pair-index construction | 3,029,417 ns | After prior class logs are loaded; target independent |
| Public-point lookup | 667 ns | Target dependent |
| Pair relation and scalar calculation | 2,791 ns | Target dependent |
| Scalar replay `86T=Q` | 7,875 ns | Target dependent |
| Interval overhead | 917 ns | Target dependent |
| Complete measured component interval | 12,250 ns | Sum of the four target-dependent entries above |

The times are one ordinary-host component run. The index contains every subgroup point at `q=199`; its coverage and preparation cost are part of the mechanism, and they make the lookup result specific to this small subgroup. Earlier curve/class construction, degree-13 lifting, relation enumeration, and anchored class-log solving are bound as separate parent receipts rather than charged to this component interval. The run retains `candidate_id: null` and `target_online_ms: null`; the complete IC candidate manifest and paired same-point rho study are future work.

`audit.json` confirms the public point, frozen scalar derivation, all 3,120 index entries and canonical index digest, first witness, group equation, scalar 86 and timing arithmetic. The checked repository Sage launcher and its runtime receipt were used for that audit. `TargetPair.lean` proves a conditional pair-to-log transport statement and the finite modular arithmetic `−163+50 ≡ 86 (mod 199)` with no axioms. The exact group relation is independently checked in Sage; the Lean proof map records this concrete bridge.

## Next experiment

The pair index saturates the order-199 subgroup. Repeat the frozen one-target procedure on a larger prime subgroup where the 3,120 signed pair patterns cover only part of the group, retain unsuccessful targets, and compare any chosen target-relation method only after a complete candidate, cold/online accounting and same-point rho reference are specified.
