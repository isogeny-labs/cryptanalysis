# Exact functional-root map and N41 solver gate

**Contribution.** A frozen exact audit represents each valid final source
code's target-conditioned pair roots by two branch bits. It reproduces all
four archived final roots for each of the 71 N41 source codes. On the N131
W29 sample, it checks 514 source codes for each of two target conditions,
recovers the constructed pair at indices `(512, 513)`, and records an empty
pair-hit set for the fixed-suffix public query in that sample. Two Boolean
encodings preserve the 33 archived positive/reachable controls. A paired
solver gate shows that the field inversions used to remove witness bits
increase search cost, so neither encoding passes promotion to an ordinary
N41 query.

## Method and exact audits

For the source quadratic `C*u²+p*u+H=0`, compute `v=C*u/p`, then
`v²+v=CH/p²`. The half trace supplies one root `v0`; the pair roots are
`u=(p/C)*(v0+b0)`, `b0 in {0,1}`. For fixed target reciprocal `t`,
put `A=1+(t*u)²`, `B=t*u`, `D=t²+u²`. The target equation
`A*w²+B*w+D=0` has roots
`w=(B/A)*(halftrace(AD/B²)+b1)`, `b1 in {0,1}`.
The audit checks `p,C,A,B != 0`, both traces zero, distinct roots,
the original two quadratics, and the archived lookup/group result for
every evaluated record. The algebraic equivalences and root completeness
are [Lean checked](PROOF_MAP.md); the concrete half-trace and curve bridge
remain explicitly recorded there.

The N41 field is `GF(2)[x]/(x^41+x^3+1)` on
`EC1N41Ckb1h7d5e80d3c4d0`. The frozen public point is
`(1936680952394, 910597499030)`. The N131 field is
`GF(2)[x]/(x^131+x^13+x²+x+1)` on
`EC1N131Ckb1heb5f1998f20b`, with curve `y²+xy=x³+1`.
Its frozen W29 input has 28 free source-code bits; 512 valid sampled codes
and two constructed-control codes make the 514-code audit domain.
The public fixed-suffix query is the archived public point minus its
frozen three-pair suffix. Results are conditioned on these exact input laws.

| Audit | Source codes | Target conditions | Root cases | Pair hits | Wall |
| --- | ---: | ---: | --- | --- | ---: |
| [N41](n41_result.json) | 71 | 1 | 71 four-root cases; no exceptions | All archived root sets match | 0.385 s |
| [N131](n131_result.json) | 514 | 2 | 1,028 four-root cases; no exceptions | Constructed: `(512,513)`; fixed-suffix public sample: `[]` | 20.256 s |

Both audits used the [checked Sage launcher receipt](sage_runtime_info.json),
one process, a 120-second wall cap and 4-GiB envelope. Their
[N41](n41_protocol.json) and [N131](n131_protocol.json) protocols pin all
source hashes before execution. The N131 finite sample is a sampled
source-bound check; the zero pair hits apply to these 514 codes and this
fixed suffix.

## Boolean construction and paired probe

The complete functional circuit has five 8-bit source codes, a 41-bit
preceding reciprocal, and two branch bits: 83 declared input bits. The
source-only variant has the same codes and preceding reciprocal, one
source branch bit, and an explicit 41-bit target root: 123 declared input
bits. The preceding two-quadratic reference uses 163 declared input bits.
Both new builds checked one archived positive and 32 reachable negative
controls; the negative controls satisfy the final root gate but fail the
preceding quartic. Each build includes all 71 allowed-code constraints,
cross-pair column disjointness, the first-three-pair norm, and the fourth
pair quartic.

| N41 circuit | Input bits | AND gates | Variables | CNF clauses | XOR rows | Build wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior two-quadratic reference | 163 | 111,680 | 128,017 | 336,899 | 16,174 | 28.387 s |
| [Source-only functional](source_build_result.json) | 123 | 115,644 | 133,601 | 348,791 | 17,834 | 32.836 s |
| [Both roots functional](build_result.json) | 83 | 133,930 | 155,382 | 403,649 | 21,369 | 41.921 s |

The formula and control-wiring hashes are in the build receipts. Build
protocols cap one worker at 240 seconds and 4 GiB. The fully functional
build used 178,421,760 B self RSS; the source-only build used
159,645,696 B self RSS. The first plain-Python launch failed on a missing
`psutil` import, and the first checked-Sage build found an omitted
Frobenius rotation in the replay fixture. Those receipts are preserved as
[environment](build_failure_0.json) and [assertion](build_failure_1.json)
failures; the corrected build used a new frozen protocol.

Each comparison used the same archived point, one CryptoMiniSat 5.14.7
worker, a 20,000-conflict cap per arm, alternating
`quadratic/variant/variant/quadratic` order, monitored 4-GiB RSS, and an
180-second parent cap. All eight arms ended `INDETERMINATE_CONFLICT_CAP`;
the conflict cap is solver work, not a relation-yield count. Each frozen
promotion gate required the variant to use at most 80% of the adjacent
reference decisions and at most 125% of its wall time.

| Variant | Paired decisions, variant/reference | Paired wall, variant/reference | Gate |
| --- | ---: | ---: | --- |
| [Both roots functional](probe_result.json) | 4.303 / 4.303 | 3.079 / 3.047 | FAIL |
| [Source-only functional](source_probe_result.json) | 1.081 / 1.081 | 1.289 / 1.671 | FAIL |

These are exploratory ordinary-host stage measurements under fixed
conflict work. The paired wall values include observed host variation;
the decision counts independently show the same direction. Neither arm
has a terminal SAT/UNSAT result. `candidate_id` remains `null`, and no
single-target online timing is inferred from these stage probes.

## Next experiment

Keep the exact two-quadratic gate and seek a code-to-source-root map with
fewer nonlinear operations. A cheap next falsifier is a frozen held-out
test of low-degree Boolean interpolation for the source root on W29 valid
codes, comparing circuit size and paired solver work with the 20,000-conflict
reference. Any favorable N41 encoding must then pass an independently
checked N131 source-bound ordinary-query gate within one worker,
600 seconds, and 4 GiB before target recovery and same-point rho timing.

Run `python3 verify.py` in this directory to recheck source hashes,
audit statuses, model controls, formula hashes, paired probe statuses,
and the Lean axiom audit. All local finite-field jobs were launched through
the repository's `./sage` wrapper.
