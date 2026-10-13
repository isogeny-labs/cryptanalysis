# Direct linked-addition proof map

| Result | Evidence | Scope |
| --- | --- | --- |
| Cleared addition equation identifies the reciprocal of the candidate sum | [`reciprocal_from_cleared_addition`](ClearedAddition.lean) | Checked parametric theorem: multiplication associativity, the field inverse law for `d²`, and the circuit equation `u·N=d²` imply `u·(N/d²)=1`. The assumptions are exposed as theorem arguments. |
| The constructed Boolean circuit enforces the cleared equation | [direct.py](direct.py), [full control](direct_control_result.json) | Complete assignment of the frozen N131 fixture satisfies every clause and native-XOR row. |
| `N=d³+s²+sd` is the numerator of the binary-curve addition x-coordinate | [RESULT.md](RESULT.md), [prior all-root addition audit](../n131_w18_linked_signature_prefix_20261012/fast_audit_result.json) | Written derivation and all-root Sage addition replay. A faithful Lean theorem over the actual GF(2¹³¹) curve is open: it needs the field model, halftrace identity, Frobenius action, and the group-law bridge. The checked parametric theorem does not replace that bridge. |
| Frozen public query and formula replay | [query receipt](query_result.json), [terminal audit](query_audit_result.json) | One worker, 600-second target-dependent cap, 4-GiB combined RSS; `BOUNDED_UNKNOWN`. The 18,387,022-byte public XCNF was rebuilt byte for byte. |

The Lean command is `lean ClearedAddition.lean` from this directory with the pinned toolchain. `lean_check.log` retains the build and `#print axioms` output. `lean4checker --fresh` is unavailable on this host. The concrete curve-action formalization is partial.
