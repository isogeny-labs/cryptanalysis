# Proof map: x-quotient target lookup

| Result | Declaration or check | Status |
| --- | --- | --- |
| If `x(L)=x(U-R)` and each x fiber is `{P,-P}`, then `L+R=U` or `-L+R=U` | `N41XQuotient.target_x_match` in `XQuotient.lean` | Checked Lean 4.34.1, no axioms. The x-fiber and group laws are explicit hypotheses. |
| Either signed completion is found by the x lookup | `N41XQuotient.target_x_complete` in `XQuotient.lean` | Checked Lean 4.34.1, no axioms. The x-negation and group laws are explicit hypotheses. |
| Binary-curve x fiber and concrete ID map `sid XOR 3` | Written proof below; exhaustive native source checks over all 840 states | Concrete bridge to Lean is open: no binary-field curve/group and state-ID encoder are formalized in this module. |
| New ten-pair witness, distinct columns, cofactor projection, folded row | `audit_sage.py`, `audit_result.json` | Independently checked Sage under pinned runtime. Concrete curve/quotient claims remain open in Lean. |

For `y²+xy=x³+1`, fixing `x` gives a quadratic in `y`. If `y` is one root, `y+x` is the other because `(y+x)²+x(y+x)=y²+xy`; degree two gives no third root. The inverse of `(x,y)` is `(x,y+x)`. At `x=0`, the roots coincide; the x-key still has the sole point and the native replay checks it. Infinity has a distinct sentinel key. Negating every point in a tuple negates its sum. In each frozen four-state edge, simultaneous sign reversal is `sid XOR 3`, which the executable checks against group negation for every slot and state before building the table.

The Lean command is `lean XQuotient.lean` with the `lean-toolchain` pinned to `leanprover/lean4:v4.34.1`. The checked command output is saved in `lean_check.txt`. Its `#print axioms` lines report no axioms for either theorem. The source uses no `sorry`, `admit`, or custom axiom. The field/curve fiber proof, finite state pairing, and relation row have independent native/Sage evidence but remain outside the formal theorem's concrete definitions.
