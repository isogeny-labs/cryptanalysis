# Symbolic four-family labels retain exact W6 output membership

An 18-primary-bit XCNF selects one of four N41 product families on each
side of the target S3 equation while keeping both output coordinates free.
The constructed positive assignment satisfies every emitted CNF and native
XOR row. On the same two regions, an exact indexed join finds its one
coordinate pair and classifies the frozen public target with zero pairs;
independent checked Sage reconstruction agrees. Both unpinned symbolic SAT
queries remained in active search through 35-second parent caps. The
experiment measures the cost of enforcing labels inside one Boolean formula
before using this representation in a larger partial-sum solver.

## Exact input and encoding

The curve ID is `EC1N41Ckb1h023d9a38bbf7` over
`GF(2)[t]/(t^41+t^3+1)`. The left product-code region is `[816,819]` and
the right is `[176,179]`, each four consecutive W6 product families.
Their relaxed pair-output spaces have dimensions `(6,6,7,6)` and
`(6,6,6,6)`. Two selector bits and seven coefficient bits on each side
produce one nonzero output in the chosen family's linear space. The circuit
then enforces the exact reciprocal link

`(tcd)^2+tcd+c^2+d^2+t^2=0`.

The constructed query uses `t=1515824644274`, with the archived witness
`(c,d)=(940337512568,1570560155378)` from product codes `(819,176)`.
The ordinary public-point query uses `t=1000731834126` and exactly the same
two regions. No coordinate or product code is pinned in either SAT formula.
The formula has 1,961 variables, 5,013 CNF clauses, 286 native-XOR rows,
1,657 AND gates, and 18 primary bits. This is a point-decomposition
component with `candidate_id: null`.

| Query | Full assignment control | CryptoMiniSat result under 35 s parent cap | Exact indexed join | Independent Sage |
| --- | --- | --- | ---: | ---: |
| Constructed positive | all rows satisfied | `BOUNDED_UNKNOWN_PARENT_CAP` | 1 pair | 1 pair |
| Frozen public target | not applicable | `BOUNDED_UNKNOWN_PARENT_CAP` | 0 pairs | 0 pairs |

Both SAT processes were active at the cap, with no solver decision line.
Their combined sampled RSS maxima were 68,829,184 and 65,159,168 bytes.
The indexed join enumerated 316 distinct left and 252 distinct right
outputs, then made 334 target-dependent quadratic-root proposals per
query. Its two queries took 3.712 and 2.200 seconds within a 6.179-second
parent run. The native runner's process-exit sampling race set
`monitor_degraded: true`; its wall, output, and sampled memory record are
preserved, but the memory sample is not a complete resource certificate.
The checked-Sage replay took 44.394 seconds under a 120-second/4-GiB cap,
with monitoring intact and sampled combined RSS 236,847,104 bytes.
These local CPU times are algorithmic diagnostics without a host-isolation
receipt.

The prior complete W6 product-span join independently found zero pairs for
this public point across all 2,048 families. This smaller, label-preserving
region check agrees with that census and supplies a matched SAT-versus-index
comparison. Run `python3 -B verify.py` to check source and result hashes,
caps, active-search evidence, exact hits, and independent Sage agreement.

## Transfer decision

The selector formula adds only four product-label bits for two four-family
regions, but it leaves the nonlinear target link to SAT. The bounded
positive shows that formula compactness alone did not give useful search
propagation on this control. The exact join wins this N41 region by
enumerating only its 316 left outputs and probing a right index, an approach
whose literal N131 W18 form still has at least `2^53` product/output
assignments before the target join. The next iteration should test a joint
condition on **two unresolved two-pair sums and the public target** that
rejects source-labeled families before output materialization, using an
unpinned W8 public relation as the correctness gate. The current experiment
adds no new mathematical theorem; its family construction and S3 identity
are inherited from the cited N41 controls.
