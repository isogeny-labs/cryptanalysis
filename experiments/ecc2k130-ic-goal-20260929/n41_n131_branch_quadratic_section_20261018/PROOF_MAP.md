# Branch-invariant quadratic-section proof map

For each frozen source code `c_i`, let `u_i` be the first half-trace pair
root and `d_i` the XOR difference to its other root. Let `phi(c_i)` be the
constant, linear and pairwise-product Boolean monomial vector. The
[certificate](certificate_result.json) gives an index set `S` and output
bit mask `L` with three directly checked properties:

1. `XOR_{i in S} phi(c_i) = 0`.
2. `parity(L & d_i) = 0` for **every sampled source code**, so this
   output bit is invariant under either root choice.
3. `XOR_{i in S} parity(L & u_i) = 1`.

Any degree-at-most-two Boolean vector map from code to a selected root
would become a linear map from `phi(c)` to the parity bit. Its output XOR
over `S` would be zero by property 1. Properties 2 and 3 force that XOR
to be one for every possible assignment of the branch bits. Therefore
the selected root cannot be degree at most two on the frozen domain,
even with a separate branch choice for every source code.

| Result | Lean declaration | Exact status |
| --- | --- | --- |
| Additive maps preserve finite sums | `BranchObstruction.map_sum` | Kernel checked for abstract zero/add operations and an explicitly additive map. |
| Branch-invariant parity excludes an additive feature fit | `BranchObstruction.no_branch_fit` | Kernel checked with explicit feature dependency, annihilated branch differences, and nonzero root parity. |
| Concrete N41 and N131 feature, root, and mask certificates | Open Lean bridge | [verify.py](verify.py) directly replays all three numeric conditions from pinned source records. A Lean encoding of those specific bit-vector certificates and the polynomial-feature correspondence is not yet complete. |

The actual module is [BranchObstruction.lean](BranchObstruction.lean),
using pinned [Lean 4.34.1](lean-toolchain). The command
`lean BranchObstruction.lean` returned exit code zero; [lean_check.log](lean_check.log)
records `#print axioms`. The structural result uses only `propext` and
`Quot.sound`. The module has no `sorry`, `admit`, custom research axiom,
or native-evaluation proof step. `lean4checker --fresh` was unavailable
on this host.
