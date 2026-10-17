# Two three-source norms coupled to one public N41 target

The circuit admits an exact archived six-pair relation while leaving all six
source codes free. It combines two three-source quadratic norms through one
Semaev-three equation on the reciprocal coordinates of their partial sums and
the public target. The ordinary one-worker CryptoMiniSat query parsed and
searched the 214,101-variable circuit for 190.056 s, recording 601 restart
lines before its parent wall cap. Its status is `BOUNDED_UNKNOWN`.

## Method and frozen instance

Each of six source slots has 40 permitted canonical W8 pair codes. The first
three source-root pairs feed one norm and the second three feed another. The
partial sums have free reciprocal coordinates `t,u`. For the public point's
reciprocal coordinate `q`, the linking equation is

`S3(t,u,q) = (t+u+q)^2 + t*u*q + (t*u*q)^2 = 0`.

The formula also excludes 690 pairs of source codes whose folded factor-base
columns collide. It is a necessary coordinate condition; a returned model
requires source-root extraction, actual point addition, and public-point replay.
The public raw target is `(2026560328086, 1928332930914)` on curve
`EC1N41Ckb1h7d5e80d3c4d0`. The six slot rotations are
`(0,6,12,18,24,30)`. This target was archived before this construction in
the independently audited [six-pair join](../n41_sixpair_shared_target_20261017/RESULT.md).
The fixed witness is used only by the circuit-control check, not as solver
assumptions. The proposal remains `candidate_id: null`.

## Results

| Stage | Result | Boundary |
| --- | --- | --- |
| First build invocation | `PRODUCER_FAILURE`, exit 1 in 0.077 s: system Python lacked `psutil` | Raw stdout/stderr and receipt retained |
| Checked-Sage retry | `COMPLETE`, 6.795 s parent wall, peak child RSS 215,597,056 B | `sage_runtime_info.json` saved before build; 3.649 s formula build, 1.113 s witness control, 0.024 s serialization |
| Public-target circuit | 186,824 AND gates; 214,101 variables; 561,815 clauses; 27,153 native XOR rows; 17,505,806 B XCNF | Known point witness satisfies every clause and XOR row |
| Ordinary public query | `BOUNDED_UNKNOWN`; 190.056 s; 601 restart lines; sampled combined peak RSS 651,739,136 B | CryptoMiniSat 5.14.7, one thread, 180 s solver setting, 190 s parent cap, 4 GiB combined RSS cap; parent sent SIGTERM at its cap; no terminal answer in raw log |
| Independent artifact audit | `PASS` | Hashes sources, binary, formula, raw logs, retained first failure, query parse/search, caps, and archived target |

The log shows 27,153 XOR clauses loaded, search beginning, and 601 restart
lines. Its `--maxnummatrices=0` setting left Gauss matrices unused; this is
part of the frozen solver configuration. The ordinary query has no verified
relation output, so relation yield and useful rank are unmeasured here. These
are stage measurements on the ordinary local host, not isolated wall-time
comparisons. [query_result.json](query_result.json) and
[solver.stdout](solver.stdout) preserve the bounded result; run
`python3 verify.py` to check the artifact chain.

## Proof and next experiment

[PROOF_MAP.md](PROOF_MAP.md) maps the structural group implication to a
kernel-checked Lean theorem and states the norm-to-curve obligations. The
theorem's `#print axioms` output is empty.

The next design change is to eliminate one 41-bit partial-coordinate vector
before Boolean search: take the quadratic resultant of the public `S3` link
and one three-source norm, then couple the resulting condition to the other
half. First measure expression size and witness preservation on this same
frozen N41 point under the 4 GiB bound. Only run an ordinary query if the
resultant reduces search state or circuit cost enough to justify it; preserve
any expansion or timeout as a separate measured result. This keeps the exact
public-target condition while moving it earlier in the algebraic pipeline.
