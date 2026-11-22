# Frozen W23 six-pair public query and XOR-matrix boundary

The corrected W23 shared-inverse six-pair circuit ran against raw preimage
zero of the frozen N131 public point for **595.039 s of target-dependent
work** under one worker and a 4-GiB combined-RSS cap. Its terminal status
is `BOUNDED_UNKNOWN`: the parent stopped the active solver at its declared
search boundary, with no SAT or UNSAT line. The full formula has **127,822
variables, 263,060 CNF clauses and 38,657 native XOR rows**. A separate
matched 100,000-conflict screen admitted ten local Gaussian matrices under
wider limits, but both matrix policies ended with **124,469 free variables**.
This directs the next iteration toward a stronger target-conditioned
multi-source constraint rather than this matrix-limit adjustment.

## Exact source and ordinary point

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, with `y²+xy=x³+1` and prime subgroup order
`680564733841876926932320129493409985129`. The public workload is
`cc09e7eb202a`, subgroup point
`(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. This query uses its archived
raw preimage zero, `(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`, whose **standard**
reciprocal x coordinate is `770794657550069419943936485965613853151`.
The six pair rotations are `(0,18,36,54,72,90)` for canonical W23 seed
`898618`.

The [earlier W23 circuit build](../n131_w23_sixpair_shared_circuit_20261017/RESULT.md)
checked a complete constructed assignment for this source law. The
[N41 same-topology control](../n41_sixpair_shared_target_20261017/RESULT.md)
found an unpinned ordinary six-pair relation and independently replayed all
twelve leaves. The [frozen protocol](protocol.json) binds those receipts,
the checked [Sage runtime](sage_runtime_info.json), source and solver binary
hashes, public point, raw-preimage choice, resource envelope and flags.
The public formula leaves cross-pair folded-column collisions to a model
check. [`audit_model_sage.py`](audit_model_sage.py) reconstructed all twelve
leaves of the constructed control, checked twelve distinct folded columns,
and found its unique raw-target signed combination among 64 choices. Its
[`model_control_result.json`](model_control_result.json) records that checked
Sage replay; the same code accepts a solver model for independent point and
column verification in a later query.

## Charged public attempt

| Exclusive target-dependent phase | Seconds |
| --- | ---: |
| Raw target to standard reciprocal | 0.068374 |
| Formula construction | 28.312248 |
| XCNF serialization | 0.010281 |
| Solver launch, search and stop | 566.647409 |
| Terminal parse and model check | 0.001041 |
| **Total** | **595.039353** |

The [query receipt](result.json) and raw [solver output](solver.stdout)
record 1,595 restart rows, no terminal status line, solver exit `-9` from
the parent cap, and 604,192,768 bytes sampled peak parent-plus-child RSS.
The solver admitted zero Gaussian matrices; its initial diagnostics reject
one `23,472 × 69,723` XOR component and four `3,315 × 9,132` components
under default limits. The [receipt audit](audit.stdout) checked source
hashes, exact XCNF header and row counts, phase sum, cap, monitor state,
raw transcript hashes and terminal classification.

The first frozen launch completed the same formula but stopped at an
artificial 20-second formula-build assertion before starting CryptoMiniSat.
Its [original protocol, runner, formula and raw failure](attempt1/FAILURE.md)
are retained. The retry changed that assertion to the declared parent cap;
both formulas have SHA-256
`7ccd6227ec72b810bf5d24ec1d6400d16c10b0e4401bb19160a2a56a683dc452`.

## Same-formula matrix-policy screen

The [matrix protocol](matrix_protocol.json) fixed this exact public XCNF,
binary, 100,000 conflicts per arm, one worker, a 100-second solver limit,
a 110-second parent limit and 4 GiB. The only changed flags were
`--maxmatrixrows=4096 --maxmatrixcols=10000 --maxnummatrices=12`.

| Policy | Admitted Gaussian matrices | Final free variables | Solver status | Parent wall | Sampled peak RSS |
| --- | ---: | ---: | --- | ---: | ---: |
| Default | 0 | 124,469 | `INDETERMINATE` at 100,000 conflicts | 11.775 s | 215,613,440 B |
| Wider limits | 10 | 124,469 | `INDETERMINATE` at 100,000 conflicts | 16.968 s | 282,181,632 B |

Both arms used the same formula and reached 336 restart rows. The
[independent log audit](matrix_audit_result.json) matched the raw status,
matrix-admission, restart, free-variable, hash and resource records. These
walls are ordinary-host diagnostics; the fixed-conflict free-variable
observation is the structural comparison. A first matrix-screen freeze
through system Python failed at `psutil` import before creating a protocol
or launching a solver; the [raw error](MATRIX_FREEZE_FAILURE.md) remains
separate from both frozen arms.

## Next algorithmic test

On the frozen N41 ordinary six-pair relation and all-valid three-bit source
flats, represent the target-conditioned three-slot Riemann–Roch determinant
as a Boolean polynomial and eliminate selector variables by the exact norm
recurrence `N_i(F)=F|_(x_i=0)·F|_(x_i=1)`. Freeze the block cover and compare
this nonlinear whole-block zero test with explicit state evaluation on the
ordinary witness and negative residuals. Charge polynomial construction,
intermediate term counts, field operations, memory and every rejected or
surviving block. The acceptance gate is lossless early rejection with an
N131 source-bound work projection that fits one worker, 600 s and 4 GiB;
only then promote to another public N131 relation query. This remains a
point-decomposition stage with `candidate_id: null`.
