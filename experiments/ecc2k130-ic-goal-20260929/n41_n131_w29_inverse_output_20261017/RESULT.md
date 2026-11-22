# Exact inverse-output source decoding and N41 solver gate

An exact five-pair circuit now derives each fixed-seed source mask from a pair output `z` and its inverse `q=1/z`. The resulting N41 circuit passes the archived public relation assignment, and an independent checked-Sage audit verifies the product formula and decoded source on all 284 signed states from its 71 canonical pair edges. In the matched 100,000-conflict public-point probe, this encoding increased AND gates from 15,047 to 21,812 and propagation from about 34 million to 38 million on the completed runs. It therefore does not pass the N41 promotion gate for a full N131 query in its current form.

## Algebra and exact circuit

The fixed-seed pair output satisfies `Cz²+pz+H=0`, where `p=a(a+s)`, `s=h²+h`, `H=h²`, and `C=1+H`. Since a usable output is nonzero, set `q=1/z`. Multiplying the quadratic by `q` gives the exact linear product identity

`p = Cz + Hq`.

The fixed-seed product map `a ↦ a²+sa` is GF(2)-linear. Restricting `a` to the canonical half-space that omits the seed's highest set bit makes it injective: its kernel `{0,s}` intersects that half-space only in zero. The implementation selects independent coordinate rows of the product map, inverts their binary matrix, decodes every source-mask bit as XORs of `z` and `q`, and checks all remaining product coordinates. It enforces `zq=1`, the exact product-inverse source gate, both endpoint inverse-trace conditions, source trace, five pair rotations, and the four balanced S3 links. The same five-output target-trace row is added to both compared circuits.

For N41, the field is `GF(2)[u]/(u^41+u^3+1)`, the curve is `y²+xy=x³+1`, the source seed mask is 56, and the public raw point is the archived orientation-3 point `(2105655159232,891719206310)`. The five pair rotations are `(0,6,12,18,24)`. The decoder uses eight source bits and independent product-coordinate rows `(2,4,6,9,10,11,12,13)`. The N131 W29 source map has rank 28 with independent coordinate rows `(2,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31)`; that algebraic check does not by itself select a degree-131 solver variant.

## Frozen N41 control and probe

The constructed five-pair assignment satisfies every CNF clause and native XOR row of both XCNFs. The independent Sage audit reconstructs the exact N41 curve, obtains `z=1/x(P)` from each archived signed pair sum, verifies `Cz²+pz+H=0` and `p=Cz+H/z`, and solves the rank-eight product map independently for the original source code. Each of the 71 edges has two reciprocal-output roots among its four signed states.

| Same public point and target-trace row | AND gates | Variables | Clauses | XOR rows | Fixed-conflict result |
| --- | ---: | ---: | ---: | ---: | --- |
| Exact source mask variables | 15,047 | 18,341 | 45,734 | 2,721 | 100,002 conflicts; 152,338 decisions; ~34M propagations |
| Masks decoded from output inverse | 21,812 | 25,576 | 66,219 | 3,026 | completed replicate: 100,002 conflicts; 151,320 decisions; ~38M propagations |

The one-worker ABBA probe used CryptoMiniSat with a 100,000-conflict flag, 90-second outer wall cap per run, and 4 GiB combined RSS cap. The first exact-source run completed `INDETERMINATE` in 62.353 s. The first inverse-output run reached the 90.033 s wall cap with no terminal solver status; its last flushed restart line was at about 99,000 conflicts. The second inverse-output run completed `INDETERMINATE` in 70.217 s. The last exact-source run emitted a normal `INDETERMINATE` result at 100,002 conflicts and exited zero after 85.686 s, while the parent recorded `MONITOR_FAILURE` in a process-exit sampling race. That monitor status remains in the raw row. Solver-reported thread times for the completed rows were 6.34 s, 6.65 s, and 6.75 s in run order, respectively. The ordinary shared host was heavily contended; these are circuit and fixed-work diagnostics, not calibrated online IC/rho measurements.

## Proof map and decision

The pinned Lean 4.34.1 file `InverseOutput.lean` checks both directions of `p=Cz+Hq` versus the characteristic-two quadratic under `zq=1`. `#print axioms` reports only the standard Lean foundations `propext`, `Classical.choice`, and `Quot.sound`, with no `sorry` or custom axiom. The binary decoder verifies full basis rank and one-hot reconstruction for every basis vector, which by GF(2)-linearity proves its inverse on the source product image; the field-specific all-state Sage audit provides an independent check of the N41 instantiation. The exact finite-field decoder and group-law bridge remain to be formalized in Lean. `lean4checker --fresh` was unavailable on this host.

The current variant is an exact structural alternative, but its larger N41 circuit and higher propagation count fail the frozen promotion gate. The next algorithmic experiment should reduce the output-inverse multiplication cost before considering W29, or use a non-additive joint target constraint that prunes whole source families. The earlier trace-character and partial-span experiments already rule out simply stacking additive parity rows or widening a low-rank span filter. A new N131 full query requires a favorable unpinned N41 gate, an independently replayed ordinary relation, and the same one-worker 600-second/4-GiB accounting. `candidate_id` remains null for this stage experiment.
