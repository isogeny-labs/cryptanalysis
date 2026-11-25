# Fixed-suffix coverage proof map

The [Lean 4.34.1 module](Coverage.lean) built with `lean Coverage.lean`.
The retained [axiom output](lean.stdout) reports `propext` and
`Quot.sound` for `reachable_length_le`, the standard foundations
`propext`, `Classical.choice`, and `Quot.sound` for the two success-count
theorems, and no axioms for the closed numerical certificates. The module
uses no `sorry`, `admit`, custom axiom, or native evaluation. A fresh
`lean4checker` binary was unavailable.

| Mathematical result | Lean declaration | Exact scope |
| --- | --- | --- |
| Concatenating bounded completion lists | `reachable_length_le` | For any list of suffixes and completion lists of length at most `M`, the concatenated list length is at most `kM`. Checked. |
| Successful targets under bounded advice | `successful_targets_le` | For distinct targets and an advice alphabet of `C` codes, if each advice code selects a completion list of length at most `K`, successful target count is at most `CK`. Checked. |
| Nested advice/suffix coverage | `bounded_advice_suffix_success` | Combines the two preceding bounds: at most `CkM` successful targets, with suffix list length at most `k` and every suffix completion list length at most `M`. Checked. |
| W29 completion count | `n131_pair_bound` | The closed integer identity `16 binom(2^28,2)=576460750155939840`, with the binomial written as `N(N−1)/2`. Checked. The four states per code and distinct-code source policy are verified in the cited source records, not formalized as elliptic-curve objects in Lean. |
| Billion-scaled W29 coverage | `n131_billion_scaled_bound` | The exact inequality `600000000000 × M × 10^9 < r`. Checked. The subgroup order is the frozen curve input, not proved by this module. |

The written group argument assigns each fixed suffix `S` a completion set
`{S+P_i+P_j}` over two distinct source codes and their at most 16 signed
states. This has cardinality at most `M`, since group-sum collisions only
identify outputs. For each advice value, at most `k` fixed suffixes expose
at most `kM` targets. Taking the union over at most `C` advice values
gives `CkM`. Dividing by `r` yields the uniform-target probability bound.
The theorem includes a complete target-conditioned advice function; its
restriction is only that the advice alphabet and the fixed suffix lists
obey their declared bounds. An arbitrary adaptive suffix generator needs
a different analysis.
