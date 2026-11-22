# Exhaustive first-code cube gate on the N41 public-target circuit

The frozen first-slot code partition covered **all 40 permitted source codes**
of the public six-pair Boolean circuit. CryptoMiniSat parsed and searched
every cube under one worker and a 12-second parent cap per cube. All 40
outcomes are `BOUNDED_UNKNOWN`; their charged query intervals sum to
**482.878 seconds**, within the 550-second aggregate cap. A retrospective
assignment check shows that one of these censored cubes is satisfiable: the
archived independently replayed six-pair relation satisfies **all 82,957
CNF clauses and 3,689 native XOR rows** of this exact public circuit.

## Construction and measured result

The circuit is the archived N41 shared-inverse six-pair formula for raw public
point `(2026560328086,1928332930914)` on curve
`EC1N41Ckb1h7d5e80d3c4d0`. It has 31,533 variables, 26,937 AND gates,
82,957 ordinary clauses, and 3,689 native XOR rows. `freeze.py` rebuilt it
with the checked repository Sage launcher and required byte-identical
SHA-256 to the archived public XCNF before any cube ran. The 40 codes were
computed from the permitted geometry and sorted numerically; the relation
witness was not read for cube ordering or solver input. Each cube adds seven
unit clauses to the same public formula. The 88 forbidden code patterns
already have exclusion clauses in that formula.

| Frozen campaign stage | Result |
| --- | ---: |
| Permitted first-slot code cubes | 40 of 40 queried |
| Per-cube solver / parent limits | 10 s setting / 12 s parent wall |
| Sum of exclusive solver intervals | 482.878 s |
| Maximum sampled parent-plus-solver RSS | 279,756,800 B |
| Aggregate logged restart lines | 15,267 |
| Terminal solver answers | 0; each row `BOUNDED_UNKNOWN` |
| Monitoring and parsing | All 40 monitors healthy; every log records XCNF parsing and search |

The first code was run as a pilot; the remaining 39 resumed the unchanged
frozen order and protocol. The public formula was built once before those
intervals; its target-dependent build, the checked-Sage startup, and
post-run verification are not included in the 482.878-second sum. The
archived identical formula build records 0.210 s for its construction and
0.003 s for serialization. This campaign is a point-decomposition search
diagnostic, with `candidate_id: null`; there is no completed target interval
to compare with rho.

After all query outcomes were frozen, `witness_control.py` reconstructed the
archived relation's six signed pair states and partial sums and checked the
full Boolean assignment on the public formula. Its first-slot numeric code
is 6; `cube_006_result.json` is `BOUNDED_UNKNOWN` after its own 12-second
cap. That establishes that the search cap censored a satisfiable cube. It
does not turn other censored cubes into UNSAT outcomes.

`verify.py` regenerates every cube byte-for-byte, checks all 40 raw logs and
hashes, verifies exact code coverage, and binds the retrospective witness
control. [PROOF_MAP.md](PROOF_MAP.md) maps the partition argument to a
checked Lean theorem and states the computational bridge.

## Decision

Splitting only the first source code did not give CryptoMiniSat enough early
propagation to resolve a cube within this 550-second aggregate envelope.
The next gate should couple at least two free code families to the public
point before restarting search. A useful cheap falsifier is a source-bound
N41 comparison of incremental learned-clause reuse or a compact algebraic
family rejection against these exact cubes, with the known-satisfiable cube
kept solely as a retrospective correctness control. Any proposed N131
transfer must still pass an unpinned ordinary N41 relation run and a
complete one-worker, 600-second, 4-GiB N131 resource projection.
