# Proof and evidence map

| Result | Declaration or evidence | Boundary |
| --- | --- | --- |
| Deduplicated output list has at most the source-list length | [`eraseDups_length_le`](TripleImageBound.lean) | Lean 4.34.1 checked; `#print axioms` reports only `propext` and `Quot.sound`. |
| Three-state image bound under source-length hypothesis `length ≤ S³` | [`triple_image_card_le`](TripleImageBound.lean) | Lean checked with the explicit list-length hypothesis. It does not assume the coverage conclusion. |
| N41 indexed three-pair group search and capped public observation | [`triple.cpp`](triple.cpp), frozen [`protocol.json`](protocol.json), [`result.json`](result.json), [`terminal_audit.json`](terminal_audit.json) | Exact tested families and cap; the public outcome is `BOUNDED_UNKNOWN` because the outer index was not exhausted. |
| Constructed five-pair control and ten signed atom/group replay | [`fixture_sage.py`](fixture_sage.py), [`control_audit_sage.py`](audit_control_sage.py), frozen control protocols and results | Checked Sage bridge for the source and concrete curve. The constructed target is separate from the frozen public point. |
| N131 W18 source count, literal index size, conditional uniform coverage | [`project.py`](project.py), [`projection.json`](projection.json), source-support digest | Exact integer census and arithmetic. The subgroup mapping to `G`, enumeration of every triple, and uniform-residual premise are outside Lean; no adaptive-target lower bound follows. |

The earlier [`common_factor_five`](../n41_common_frob_factor_20261012/CommonFactor.lean) theorem supplies the additive Frobenius identity used to pass from a projected five-pair target to its original public point. The new Lean theorem concerns the three-pair output image; a future compressed membership algorithm would need its own correctness proof and concrete source bridge.
