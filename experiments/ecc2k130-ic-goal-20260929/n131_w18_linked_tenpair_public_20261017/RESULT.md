# Linked W18 ten-pair circuit on the frozen N131 public point

**Sharing a source edge and pair-output x root across Frobenius rotations
0 and 16 reduced the frozen ten-pair circuit by 6,683 AND gates and 7,966
variables in its constructed control.** The complete assignment satisfied
all 507,226 clauses and 80,191 native-XOR rows. An independent checked-Sage
reconstruction verified the ten signed pair outputs, their constructed raw
sum, and 18 distinct folded columns. The ordinary N131 public-point query
ran for **600.059386 seconds** of target-dependent work, then stopped at its
declared timeout with status `BOUNDED_UNKNOWN`.

## Source and target-conditioned equation

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t¹³¹+t¹³+t²+t+1)`, with `y²+xy=x³+1`, cofactor four and prime
subgroup order `680564733841876926932320129493409985129`. The W18
seed-212 source has 33,191 eligible edge codes. Ten pair slots use
rotations `(0,16,32,48,64,80,96,112,128,8)`. Slots 0 and 1 share a
source code and unrotated pair-output reciprocal, leaving nine independent
edge choices. All other edge choices are shielded against the repeated
edge's folded columns and each other. The linked pair-output signs are
free when x roots are lifted; the [proof map](PROOF_MAP.md) gives the exact
same- and opposite-sign relation coefficients.

The target selector retains all four raw preimages and all 131 Frobenius
positions of the one frozen public workload `cc09e7eb202a`. Each of the
nine balanced S3 links is conditioned on the selected public reciprocal.
The [protocol](protocol.json) fixed the source hashes, target, one worker,
600-second target-dependent cap, 4-GiB sampled combined-RSS cap, and solver
flags before either formula was built. The [checked-Sage runtime](sage_runtime_info.json)
was saved before measurement. The earlier [linked N41 public relation and
N131 source census](../n41_n131_linked_frobenius_pair_20261012/RESULT.md)
provide the unpinned control and a conservative 71.598 uniform-mapping
mean for its same-sign subset. That number is a source-count heuristic,
not a measured hit rate on this public point.

## Constructed control and bounded public attempt

| Exact stage | Linked result | Archived unlinked ten-pair control |
| --- | ---: | ---: |
| Control AND gates | **165,875** | 172,558 |
| Control variables | **250,823** | 258,789 |
| Control CNF clauses | **507,226** | 528,850 |
| Control native-XOR rows | **80,191** | 81,064 |
| Complete control assignment | all clauses and XOR rows pass | archived pass |

The independent [Sage control](control_sage_audit.json) rebuilds both
source endpoints for all ten slots, identifies the signed output behind
each archived x root, verifies the linked Frobenius point, and sums the
points to the constructed raw target. A second checked-Sage
[eigenvalue audit](lambda_sage_result.json) identifies the actual subgroup
Frobenius root and verifies that both allowed repeated-column sign factors
are nonzero. The prior assumption that *both* characteristic roots act on
the rational subgroup was corrected in a retained
[failure transcript](link_coefficients_attempt1.stderr).

| Exclusive ordinary public-query phase | Seconds |
| --- | ---: |
| Four raw fibers and target Frobenius orbit | 0.135924 |
| Formula construction | 5.352473 |
| XCNF serialization | 0.030777 |
| Solver launch, search and stop | 594.537350 |
| Terminal parse | 0.002861 |
| **Target-dependent total** | **600.059386** |

The ordinary formula has **250,838 variables, 165,879 AND gates, 507,238
CNF clauses and 80,202 native-XOR rows**. Its one-worker CryptoMiniSat
process had 3,059 logged restart rows and 55 Gaussian matrix size lines.
The parent stopped it at the 600-second sampled deadline; the 59-ms
monitoring overshoot is included in the total. Sampled combined peak RSS
was **568,672,256 B**, below 4 GiB. Its transcript contains no terminal
SAT/UNSAT status and no model. The [query receipt](query_result.json) keeps
the exclusive phases, exit `-9`, exact source and formula hashes, and
bounded classification.

The original full XCNF files were archived as deterministic
[constructed](control.xcnf.gz) and [public](ordinary.xcnf.gz) gzip streams.
The independent [first audit](audit_result.json) checked their raw bytes,
headers, row counts, solver logs, phases and cap before archival. The
[archive audit](archive_result.json) checks the decompressed bytes against
the same hashes and row counts; the [read-only terminal verifier](verify.py)
reruns that check from the committed archives. Raw solver stdout and stderr
remain saved. These are ordinary-host decomposition-stage measurements;
`candidate_id` remains `null` while the complete IC pipeline is unresolved.

## Next algorithmic test

The linked x root removed one pair-source circuit but left the same balanced
S3 target search, which reached its cap. A more structural linked block uses
adjacent Frobenius rotations: for a nonexceptional point on this binary
Koblitz curve, direct addition gives
`x(P+τP)=x(P)+1/x(P)`. This maps two linked orbit appearances to one
low-degree coordinate equation and could replace an S3 leaf rather than
only sharing its source witnesses. Prove that identity with exact
exceptional cases, test both signs on the frozen unpinned N41 public
relation, measure the full circuit reduction, and derive a source-bound
N131 projection before another 600-second ordinary query. Any returned
relation must be lifted and independently replayed before factor-log and
single-target online/rho stages.
