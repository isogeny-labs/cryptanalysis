# Prefix partition proof map

The source code is an eight-bit integer `c`. Its high three bits select
`k = c / 32`. For `0 ≤ c < 256`, exactly one `k` lies in `{0,…,7}`. In
branch `k`, three unit clauses fix code wires 6, 7, and 8 (the source
code bits numbered 5, 6, and 7) to the bits of `k`. The other five bits
and all four other pair slots remain free. The eight formulas thus cover
the original formula without changing any satisfying assignment outside
the chosen prefix.

| Result | Lean declaration | Exact scope | Build and axioms |
| --- | --- | --- | --- |
| Prefix in range | `PrefixPartition.prefix_in_range` | `∀ c : Nat, c < 256 → c / 32 < 8` | Checked; `propext`, `Quot.sound` |
| Prefix interval | `PrefixPartition.prefix_interval` | `∀ c k : Nat, c / 32 = k ↔ 32*k ≤ c ∧ c < 32*(k+1)` | Checked; `propext`, `Classical.choice`, `Quot.sound` |
| Restriction preserves a matching assignment | `PrefixPartition.matching_restriction` | For any type and predicates, a base assignment with `code / 32 = k` satisfies their conjunction | Checked; no axioms |

The theorem is arithmetic and logical; it does not encode the XCNF or
elliptic-curve law. The read-only [verifier](verify.py) checks the bridge
for the executed circuit: the 71 distinct allowed codes are in `[0,256)`,
the actual first-slot wires are `[6,7,8]`, the eight source counts sum to
71, and each branch formula is byte-for-byte the frozen base formula with
the corresponding three unit clauses and updated clause count. Its hash
must match the run receipt. The predecessor's checked final-pair resultant
and positive control establish the algebraic circuit boundary separately.

Build command from this directory: `lean PrefixPartition.lean`. The pinned
`lean-toolchain` is `leanprover/lean4:v4.34.1`; [lean.stdout](lean.stdout)
contains the actual `#print axioms` output and `lean.stderr` is empty.
The initial parser error from using Lean's reserved identifier `prefix` is
retained as `PrefixPartition_attempt1.lean` with its output.
