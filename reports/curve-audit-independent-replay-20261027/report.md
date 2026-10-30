# P-192/P-224 curve-audit certificates: independent replay

**Dated followup, 2026-10-27 05:49 UTC:** A fresh native Rust build found and
repaired a pinned `sha2` compilation error. The repaired package passed all
15 tests, and fresh P-192/P-224 CLI audits matched the archived mathematical
fields. See the [separate native validation report](native-rust/report.md),
[raw receipts](native-rust/native-cli-receipt.json), and
[current followup PDF](native-rust/report.pdf). The text and PDF below retain
the original independent-Python packet's earlier execution boundary.

2026-10-27 UTC · Conductor T-499 · producer commit
`dc73f9791dc7d2c61e0c77572d2c3aaeedb30436` · review branch checker commit
`b0f44d3`. This is a deterministic validation of archived claims, not a new
performance measurement or an official research decision.

## Scope and result

The precommitted [plan](replay-plan.md) and [SHA-256 input inventory](input-hashes.json)
bind four Rust source files and the input, recursive prime certificate, Rust
audit, and Sage replay JSON for each curve. The [independent Python checker](replay.py)
uses exact integers and its own affine point law. It does not call the Rust
auditor or Sage. Its successful [result](result.json) and
[execution receipt](execution-receipt.json) show:

| Check | P-192 | P-224 | Scope |
| --- | ---: | ---: | --- |
| Recursive Lucas prime-certificate nodes | 9 | 8 | Complete `n-1` factorizations and witnesses for both `p` and `r` accepted; small factors checked by exact trial division. |
| Small prime factors checked | 41 | 40 | Exact arithmetic, not a probable-prime screen. |
| Curve and generator | pass | pass | Nonsingular, canonical affine point on the curve; independent scalar multiplication gave `[r]G=O`. Prime `r` and nonidentity imply exact point order `r`. |
| Candidate `N` | pass | pass | `r|N`, `|N-(p+1)|²≤4p`, and `r²>16p` hold using exact integers. |
| Archived Rust/Sage fields | match | match | Source digest, input/certificate hashes, candidate order, trace, twist order, and status fields agree with the newly computed values. This is consistency, not authenticated execution. |
| Mutation controls | 5 rejected | 5 rejected | Wrong input hash, witness `1`, altered factor exponent, off-curve generator, and `N+1` each failed at the intended check. |

Both inputs use `r=N`. The exact `p`, `r`, `N`, trace, and twist-order values,
control failure reasons, and source digest are preserved in `result.json`.
The historical parameters are from [NIST FIPS 186-4 Appendix D.1.2](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.186-4.pdf),
which is withdrawn as a current standard. The standard is a parameter
reference here, not an execution receipt or a claim of present compliance.

## Execution record and trust boundary

The first attempt at checker commit `95a1cce` exited 1 at module load: this
host's Python 3.9 does not evaluate a PEP 604 union in a type alias. Its
[stderr](attempt-1.stderr) and empty [stdout](attempt-1.stdout) are retained.
The type alias was repaired, committed as `b0f44d3`, and the exact committed
script then ran with `python3 -I replay.py` and exited 0. The final
[stderr](run.stderr) is empty. The receipt records the script, manifest,
result, and stderr digests. The script bytes matched commit `b0f44d3` when
the receipt was written. These are reproducibility checks, not independent
attestation of the process.

The replay verifies the concrete **certificate inference** in a separate
implementation. Its use of Hasse's theorem, Lagrange's theorem, Fermat
inversion, and Lucas's primality criterion remains mathematical reasoning,
not a Lean proof of the exact curve facts or of the Rust code. The archived
Sage report says `E.cardinality()` and point order matched the claims;
[Sage's documentation](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_finite_field.html)
defines that API as returning the number of rational points. No Sage
executable was available on this host, so this packet does not authenticate
that archived execution or supply a fresh independent point count.

Fresh native Rust build/test and CLI audit were also not run in this packet.
At execution time, other owned Lean and optimized Rust builds were active;
the requested memory-heavy serialization could not be established. This is
`not_executed`, not a passing Rust runtime verdict. The validated arithmetic
does not certify every parser branch, catalog criterion, extension-field
path, or security property of the curves. The [Hasse theorem review PR #1197](https://github.com/isogeny-labs/cryptanalysis/pull/1197)
establishes only the conditional interval-uniqueness Lean lemma. The formal
prime-field, elliptic group, exact-order, Lagrange, Hasse and interval bridges
remain open.

The [evidence diagram](certificate-boundary.svg) separates independently
replayed facts, historical report consistency, and the formal proof gap. No
timings or performance outcomes were produced, so this review does not
change a performance dashboard or canonical metric graph. The companion
[PDF](report.pdf) is generated from `report.typ` with the diagram embedded
and must be inspected after rendering.

## Next verification

When a coordinator grants exclusive memory-heavy ownership and capacity,
run the pinned `ca-curve-audit` package tests and CLI against these exact
inputs and the five mutations, recording fresh stdout, stderr, exit codes,
toolchain and dependency versions. Obtain a fresh Sage point count if a
verified Sage runtime is available. Continue the Lean bridge separately; do
not promote this packet into a full formal curve-order theorem.
