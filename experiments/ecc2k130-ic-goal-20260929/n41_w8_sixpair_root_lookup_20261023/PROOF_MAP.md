# Proof map: coherent signs in a six-leaf sum tree

| Mathematical result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Negating a representative preserves its sign class | `TreeLift.signed_neg` | Arbitrary type `G` with `Lean.Grind.AddCommGroup G`; `Signed x a` means exactly `x=a` or `x=-a`. Checked. |
| A local link realizes either chosen sign of its parent | `TreeLift.link_lift` | Same group; `Link a b c` supplies representatives of `a,b` whose sum is a representative of `c`, and the requested `t` is a representative of `c`. Checked. |
| Five local balanced links admit a coherent six-leaf sum | `TreeLift.six_leaf_lift` | Same group; exactly the five links `(p0,p1)->s01`, `(p2,p3)->s23`, `(p4,p5)->s45`, `(s01,s23)->s0123`, `(s0123,s45)->target`. No distinctness, finite-field, or curve assumptions are hidden. Checked. |

The readable proof is the recursive construction: choose representatives at the root. At each child link, choose its supplied representatives if their sum has the requested sign; otherwise negate both. Negating both preserves each child's sign class and flips the sum. Recurse down the two subtrees. Associativity then identifies the balanced sum with the six-leaf sum. This applies even when a point is its own negative.

The exact reciprocal `S3` equation used by the circuit must be bridged to the abstract `Link` predicate for all coordinate cases before `six_leaf_lift` becomes a full curve-level theorem. The independent checked-Sage sign audit verifies the table-side premise for all 480 source-root pairs: each contains distinct points summing to the identity. The constructed witness independently replays the actual group sum. The Lean theorem does not assert that an arbitrary SAT model is a curve relation, and the exceptional-coordinate bridge is open.

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`. Build command: `elan run leanprover/lean4:v4.34.1 lean TreeLift.lean`. The actual module built successfully; `#print axioms` for all three theorems reports only standard Lean `propext`, with no `sorry`, `admit`, custom axiom, or native-evaluation certificate. Output is retained in `lean_check.log`. `lean4checker --fresh` was unavailable on this host.
