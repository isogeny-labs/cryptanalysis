# Proof and audit map

| Result | Exact hypotheses and scope | Verification |
| --- | --- | --- |
| Two roots of a binary quadratic differ by the linear coefficient divided by the quadratic coefficient | In a commutative characteristic-two ring, if `C*d=p` and `C*a²+p*a+h=0`, then `C*(a+d)²+p*(a+d)+h=0`. The W20 instantiation has `C=1+h_seed²`, nonzero `p=x(x+s)`, and `d=p/C`. | `RootOffset.root_shift` in `../n41_w8_functional_root_table_v2_20261013/RootOffset.lean` is kernel-checked with no axioms; its `lean_check.log` contains `#print axioms`. This experiment checks both instantiated roots for every computed valid W20 code. |
| Half-trace root construction | For `d=p/C` and `u²+u=h*C/p²`, the element `a=d*u` solves `C*a²+p*a+h=0`; the other root is `a+d`. The half-trace identity applies because the valid source pair supplies roots. | `screen.py` checks `u²+u` and both quadratic equations on all 16,548 computed codes. The independent `audit_sage.py` recomputes the identities for all 4,184 codes in prefix zero and checks eight codes by source-point addition. The abstract construction implication is proved by direct distributivity in this note; its explicit Lean formalization and concrete `GF(2^131)` bridge remain open. |
| Shared OBDD node counts on four selected 14-bit subcubes | For each valid code in a subcube, the output is the 131-bit half-trace root or the smaller encoded root. Invalid source codes are don't-care leaves. The producer uses a low-bit-first bottom-up node reduction with shared nodes across output bits. | `result.json` records all 16 `(prefix, width)` rows. `audit_result.json` independently recomputes the complete prefix-zero width-14 row with high-bit-first top-down recursion and matches both root conventions' node counts and output roots. This is a measured representation, not a minimum BDD size over all don't-care completions or variable orders. |

For the half-trace implication, substitute `a=d*u` and `p=C*d`:

`C*a²+p*a+h = C*d²*u² + C*d²*u + h = C*d²*(u²+u)+h`.

Since `d=p/C`, the half-trace right side is `h*C/p² = h/(C*d²)`, so the expression equals `h+h=0` in characteristic two. The two roots differ by `d` by the checked `RootOffset.root_shift` theorem. The exact field, source table, code law, and sampled curve point operations are bound by `protocol.json` and `audit_protocol.json`; a formal Lean model of those concrete data remains to be built.
