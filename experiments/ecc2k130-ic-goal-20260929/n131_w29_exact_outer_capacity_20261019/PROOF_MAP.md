# Proof map: complete W29 fixed-outer capacity

| Result | Lean declaration and exact scope | Concrete bridge |
| --- | --- | --- |
| A finite advice alphabet with `C` values and at most `K` covered targets per advice value covers at most `C K` distinct targets | `ExactCapacity.successful_targets_le`, for arbitrary target/advice types, duplicate-free target list and explicitly bounded coverage lists. Kernel checked. | For one fixed outer triple, successful targets are a translate of the right two-pair sum set. A list of at most `k` triples covers at most `k M` targets, with `M` the set-size ceiling. |
| Complete W29 source gives at most 268,439,344 signed states per rotated right slot | `ExactCapacity.exactStateUpper`, exact arithmetic from 67,109,836 valid codes and four signed pair states per code. Kernel checked. | The full Gray-order producer and independent numeric-order census agree on all `2^28` codes; nonzero pair outputs were checked over the full source. Duplicate points or column exclusions can only reduce the set. |
| Ordered right two-pair sum set has at most 72,059,681,407,150,336 elements | `ExactCapacity.exactPairUpper`, exact square of the state ceiling. Kernel checked. | A group addition maps each ordered pair of states to at most one sum. Subgroup projection cannot increase cardinality. The two right rotations need not be equal. |
| Half-success arithmetic thresholds for `k=1,6,8,20,000,000` | Eight named `ExactCapacity` threshold theorems, each checking the inequality immediately below and at the stated bit count. Kernel checked without axioms. | Divide the finite-target ceiling `C k M` by the exact prime subgroup order `r=680564733841876926932320129493409985129` under the declared uniform-subgroup target law. |

**Readable proof.** For each advice value `a`, fix its list of at most
`k` outer triples. Each triple's translated right-completion set has at
most `M` points, so the union for `a` has at most `k M` points. Across
`C` advice values, at most `C k M` targets are covered. A sequence
whose only feedback before success is a yes/no completion answer has a
fixed all-negative proposal path for each advice value; its first-hit
coverage is contained in the same union. For a uniform point in the
prime subgroup, success probability is at most `min(1,C k M/r)`.

The proof applies to the stated **fixed-proposal-per-advice model**. A
method deriving more information from the public target while solving
several free source families jointly can escape its premise. The
`k=6,8` choices are exact conditional arithmetic; their connection to
a 600-second run uses observed ordinary-host terminal intervals and is
a projection, not a machine-independent throughput theorem.

The toolchain is pinned to Lean 4.34.1 in `lean-toolchain`; run
`lean ExactCapacity.lean`. Saved `lean.stdout` contains all twelve
`#print axioms` audits: only standard `propext`, `Classical.choice`,
and `Quot.sound` occur in the structural list theorems, and every
arithmetic result is axiom-free. There are no proof placeholders or
claim-encoding axioms. `lean4checker --fresh` was unavailable on this
host. A fully formal finite-field definition of the source and curve
is not in this module; the concrete source bridge is audited by the
frozen full-domain native and checked-Sage records.
