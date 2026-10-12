# Proof map for the seven-pair source count

The checked structural result is that selecting distinct folded columns for
seven pair edges and a two-column terminal state is equivalent to selecting a
graph matching that avoids the terminal columns. This is the reduction used
by `count.py` before its exact finite census.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Distinct columns of any finite list of source edges exactly characterize a matching | `SevenPairSource.columns_nodup_iff_matching` | Any `List Edge`; each edge has a source ID and two `Nat` column labels. **Checked.** The recursive matching condition requires distinct endpoints and disjointness from all later edge endpoints. |
| Distinct columns after adding one terminal state exactly characterize a terminal-avoiding matching | `SevenPairSource.terminal_distinct_iff_matching` | Any two `Nat` terminal columns and any `List Edge`; the terminal columns must differ. **Checked.** |
| The N131 four-seed source has the 32 stated seven-edge matching counts and labeled-tuple mean `1455483251861877066174773940398916548689920 / 680564733841876926932320129493409985129` | Open | **Partial formalization.** The finite census is computed by `count.py` against the hashed W18 support and terminal data in `result.json`. No Lean theorem yet connects those concrete files to the `Edge` list, proves the component matching-polynomial recurrence, checks all 32 polynomial evaluations, or formalizes the four raw-fiber group-output map and uniform-point averaging. The numerical result retains its independent Python cross-checks and is not reported as Lean-proved. |

The mathematical proof is as follows. A source pair has two folded-column
endpoints. Two chosen pairs may coexist precisely when their endpoints are
disjoint. Requiring every chosen endpoint to differ from both terminal
endpoints is exactly matching in the graph after those terminal vertices are
removed. Each edge retains its source ID, so even if multiple source pairs
share endpoints, their multiplicity is represented without identifying the
pairs. For each terminal state, the counter's matching-polynomial coefficient
at degree seven counts unordered eligible selections. Ordering their seven
slots gives `7!` labels and the four signed choices per pair give `4^7`
labels. Summing over 32 terminal states, multiplying by four raw fibers, and
dividing by the subgroup order gives the displayed labeled mean. A group
output can have several source labels, so this mean bounds the mean count of
distinct represented outputs from above.

The Lean module uses only `Std` bundled with pinned
`leanprover/lean4:v4.34.1` (Lean commit
`5045d0056413266e57c625dcd7c365b10e377c52`). On macOS ARM64, run from
this directory:

```sh
lean --version
lean MatchingCount.lean
```

The build exited 0. Its two `#print axioms` audits reported only Lean's
standard `propext` and `Quot.sound` foundations. The module contains no
`sorry`, `admit`, custom axiom, or native computation proof. `lean4checker`
was absent on this host, so a fresh checker replay remains open. The pinned
module SHA-256 at this addition is
`35a1c36cc62988e511eeae420b270df8f8ef349f0fc036e6eba2a3d8bd42dad9`.
