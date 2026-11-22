# Functional S3 middle constraint on an N41 public relation

The new circuit represents each of four S3 middle links with a reciprocal,
one trace check, and one branch bit. The complete archived N41 public
relation satisfies its 129,763 CNF clauses and 5,272 native XOR rows.
The branch-completeness theorem is checked in Lean 4. On the same five
fixed pair outputs, direct characteristic-two root enumeration tested eight
middle tuples in 0.00741 seconds and retained the unique tuple matching
the public target. The SAT query over the fixed outputs reached its
60-second cap with status `BOUNDED_UNKNOWN`.

## Instance, method, and controls

The curve ID is `EC1N41Ckb1h7d5e80d3c4d0`: `GF(2^41)` with polynomial
modulus `x^41+x^3+1`, binary Koblitz `b=1`, subgroup order
549,756,390,943, and cofactor four. The source has seed mask 56 and ten
free code bits. Five source pair outputs are Frobenius rotated by
`[0,0,12,12,24]`. The archived [public fixture](../n41_n131_w29_rotation_alignment_20261017/n41_model_fixture.json)
and [independent group audit](../n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json)
fix the target and complete relation. The [checked Sage runtime](sage_runtime_info.json)
was captured before the runs.

For each S3 link, set `B=ab`, `A=B²+1`, `D=(a+b)²`, and introduce `v`
with `Bv=1`. The circuit computes `q=ADv²`, requires `Tr(q)=0`, computes
`h=halftrace(q)`, and constrains `Az=B(h+ε)` with Boolean `ε`. It also
retains the original `Az²+Bz+D=0`. The exact branch theorem, including
`A=0`, is in [PROOF_MAP.md](PROOF_MAP.md). The generated formula and its
complete constructed assignment are recorded by [n41_build_result.json](n41_build_result.json).

| Arm | Frozen inputs | Status and observation | Wall time | Sampled peak combined RSS |
| --- | --- | --- | ---: | ---: |
| Circuit build and complete witness check | Public relation fixture | `PASS_N41_W11_FUNCTIONAL_S3_CONSTRUCTED_CONTROL`; 48,965 variables, 42,942 AND gates | 0.619 s | See build receipt |
| Ordinary one-worker query | Public point; five source codes, outputs, and S3 middles free | `BOUNDED_UNKNOWN`, `WALL_CAP`; no solver terminal | 600.049 s query; 600.668 s build plus query | 397,180,928 B |
| Fixed-input control | Five archived codes and outputs fixed; S3 middles free | `BOUNDED_UNKNOWN`, `WALL_CAP`; no solver terminal | 60.040 s | 114,442,240 B |
| Direct S3 replay | The same five outputs, rotations, and public target | `PASS_N41_FUNCTIONAL_S3_DIRECT_FIXED_REPLAY`; eight tuples, one target-compatible | 0.00741 s internal checked-Sage computation | Not sampled |

The SAT runs used CryptoMiniSat 5.14.7 with one worker, a 4 GiB RSS cap,
and frozen 590/600-second and 55/60-second solver/parent caps. The direct
resolver used one checked Sage process on the ordinary host; its internal
time excludes launcher startup. These are stage diagnostics under different
algorithms and timing boundaries. The fixed-input case measures an
archived constructed relation, not ordinary-query relation yield. Every
run retains its protocol, source hashes, stdout/stderr, cap status, and
resource receipt. `candidate_id` remains `null`.

## Interpretation and next experiment

The functional branch theorem establishes exact coverage of S3 roots, and
the complete witness check establishes that this implementation accepts the
archived relation. Adding four functional S3 links expanded the previous
N41 width-11 circuit from 19,150 variables and 48,193 clauses to
48,965 variables and 129,763 clauses. The ordinary query and fixed-input
control both remain `BOUNDED_UNKNOWN` at their caps. The direct fixed-input
enumeration shows that explicit root resolution is fast once pair outputs
are known; the expanded SAT representation did not transmit that advantage
through the solver in this configuration.

The existing [N41 two-plus-one indexed join](../n41_target_conditioned_2p1_join_20261018/RESULT.md)
already supplies an exact target-conditioned family filter: a missing
left-pair sum key rejects an entire family before witness expansion. Its
N41 public relation was independently replayed. The next iteration should
replace that join's explicit left-pair table with an **implicit exact
membership and witness oracle** for the key, then measure rejection,
lookup cost, memory, and natural public-query yield on its frozen keys.
The direct S3 result here provides a fast final check after candidate pair
outputs are identified; the unresolved step is finding those pair outputs
without a quadratic table or a broad Boolean search.
Only a successful ordinary N41 query with independent replay opens the
frozen N131 promotion gate. The later single-target comparison will charge
all target-dependent IC work and pair it with same-point rho.

Reproduce the receipt checks with `python3 audit.py`; the archived
[terminal audit](terminal_audit.json) verifies five frozen protocols and
35 source hashes. Run the two builders and both SAT queries only with fresh
output paths, since they refuse to overwrite earlier measurements. All
local Sage jobs use the repository `./sage -python` launcher.
