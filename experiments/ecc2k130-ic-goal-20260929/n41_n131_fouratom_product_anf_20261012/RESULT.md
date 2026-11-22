# Joint source-product ANF for the four-atom target equation

**Result.** Substituting two still-free seed-conditioned product subspaces into the exact four-atom eliminant produces a degree-six Boolean ANF. On the frozen N41 positive four-atom block it has **4,026 nonzero monomials in 14 product bits**. An independent full 16,384-assignment truth table found **exactly one** zero of the target-conditioned equation; the separately fixed coordinate found **zero**. On the archived N131 W15 constructed block, the same construction has **220,172 nonzero monomials in 28 product bits**, built in 0.563 s with 19.1 MB sampled process RSS. This gives a concrete joint zero-predicate encoding with both source products unresolved.

## Exact source and method

The [frozen protocol](protocol.json) binds the native source and binary, four exact input rows, the inherited 266-term eliminant, one worker, a 120-second wall cap for each run, and a 4-GiB RSS acceptance ceiling. N41 uses `GF(2)[t]/(t^41+t³+1)`, W8 source seeds `(94,171)`, rotations `(14,21)`, and the [frozen positive and negative block outputs](../n41_symbolic_seed_fiber_20261012/panel.json). N131 uses `GF(2)[t]/(t^131+t^13+t²+t+1)`, the archived W15 seed 13686 at rotations `(26,39)`, and the [constructed positive and field-control outputs](../n131_w15_rotated_fouratom_inverse_20261010/control_result.json). The source masks in the inputs reproduce the archived positive product witnesses.

For each source seed `s`, the pair product `p=w²+sw` lies in an `F₂`-linear image of dimension `d−1`. The native producer constructs independent image bases for the two rotations, writes `p=Σ x_i v_i` and `q=Σ y_j w_j`, specializes the eliminant `H(a,b,p,q,z)`, and multiplies its Boolean monomials with idempotent variables (`x_i²=x_i`, `y_j²=y_j`). The resulting field-valued ANF is zero exactly when the specialized eliminant is zero for those product choices. The producer compares this identity at the known source products and 32 fixed pseudorandom product assignments in every case. The [independent audit](audit.py) uses separate integer-field arithmetic and Boolean-polynomial code to reproduce both N41 ANFs and the N131 positive ANF. For N41 it also derives coefficients by a full truth-table Möbius transform and checks every coefficient against the symbolic producer.

| Fixed seed/output case | Free product bits | Nonzero ANF monomials | Maximum observed degree | Complete relaxed product-bin zeros | Native construction | Sampled native RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| N41 positive | 14 | 4,026 | 6 | **1 / 16,384** | 0.0034 s | 2.0 MB |
| N41 field control | 14 | 4,026 | 6 | **0 / 16,384** | 0.0026 s | 2.0 MB |
| N131 constructed positive | 28 | 220,172 | 6 | Not enumerated | 0.563 s | 19.1 MB |
| N131 field control | 28 | 220,172 | 6 | Not enumerated | 0.358 s | 18.8 MB |

The N41 zero counts cover the **full linear product images**, 128 choices per seed, before rational-source and distinct-column filtering. The one positive root therefore survives the relaxed test; the [archived checked group witness](../n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json) supplies its source validity. The field-control zero count is an exact miss for these two seed images. The N131 count is a construction-stage measurement on an archived source-derived output. Neither table row measures an ordinary public-point relation rate or complete IC online time. CPU intervals are exploratory on an unisolated host.

The [four native results](n41_positive.json), [independent replay](audit.json), and [protocol](protocol.json) preserve source hashes, monomial/degree counts, source-witness checks, direct-evaluation checks, and resource observations. The independent replay checked the two N41 cases and N131 positive case; the native run checked all four. Its first invocation failed because this host's default Python lacks `int.bit_count`; [the failure receipt](audit_attempt1_failure.json) records that audit infrastructure error. The corrected audit uses a portable popcount and passed.

## Next method gate

This ANF is a joint product-family constraint for one supplied four-atom output and seed pair. The next experiment is an exact N41 native-XOR SAT or algebraic solver for this fixed-seed ANF, paired against the existing one-sided GCD oracle on the same positive and negative coordinates. If it improves the charged inverse cost or gives stronger early propagation, extend seed selection and the upper public-target S3 equation, then require an unpinned eight-column N41 relation before an ordinary N131 attempt. `candidate_id` remains null until the full pipeline and target handling are specified.
